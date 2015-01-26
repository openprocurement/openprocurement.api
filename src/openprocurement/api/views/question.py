# -*- coding: utf-8 -*-
from logging import getLogger
from cornice.resource import resource, view
from openprocurement.api.models import Question, get_now
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    error_handler,
    update_journal_handler_params,
)
from openprocurement.api.validation import (
    validate_question_data,
    validate_patch_question_data,
)


LOGGER = getLogger(__name__)


@resource(name='Tender Questions',
          collection_path='/tenders/{tender_id}/questions',
          path='/tenders/{tender_id}/questions/{question_id}',
          description="Tender questions",
          error_handler=error_handler)
class TenderQuestionResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_question_data,), permission='create_question', renderer='json')
    def collection_post(self):
        """Post a question
        """
        tender = self.request.validated['tender']
        if tender.status != 'active.enquiries' or get_now() < tender.enquiryPeriod.startDate or get_now() > tender.enquiryPeriod.endDate:
            self.request.errors.add('body', 'data', 'Can add question only in enquiryPeriod')
            self.request.errors.status = 403
            return
        question_data = self.request.validated['data']
        question = Question(question_data)
        tender.questions.append(question)
        if save_tender(self.request):
            update_journal_handler_params({'question_id': question.id})
            LOGGER.info('Created tender question {}'.format(question.id), extra={'MESSAGE_ID': 'tender_question_create'})
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Questions', tender_id=tender.id, question_id=question.id)
            return {'data': question.serialize("view")}

    @view(renderer='json', permission='view_tender')
    def collection_get(self):
        """List questions
        """
        return {'data': [i.serialize(self.request.validated['tender'].status) for i in self.request.validated['tender'].questions]}

    @view(renderer='json', permission='view_tender')
    def get(self):
        """Retrieving the question
        """
        return {'data': self.request.validated['question'].serialize(self.request.validated['tender'].status)}

    @view(content_type="application/json", permission='edit_tender', validators=(validate_patch_question_data,), renderer='json')
    def patch(self):
        """Post an Answer
        """
        tender = self.request.validated['tender']
        if tender.status != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update question in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            LOGGER.info('Updated tender question {}'.format(self.request.context.id), extra={'MESSAGE_ID': 'tender_question_patch'})
            return {'data': self.request.context.serialize(tender.status)}
