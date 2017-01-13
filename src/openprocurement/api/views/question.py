# -*- coding: utf-8 -*-
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    apply_patch,
    save_tender,
    opresource,
    json_view,
    context_unpack,
    APIResource,
)
from openprocurement.api.validation import (
    validate_question_data,
    validate_patch_question_data,
)


@opresource(name='Tender Questions',
            collection_path='/tenders/{tender_id}/questions',
            path='/tenders/{tender_id}/questions/{question_id}',
            procurementMethodType='belowThreshold',
            description="Tender questions")
class TenderQuestionResource(APIResource):

    def validate_question(self, operation):
        tender = self.request.validated['tender']
        if operation == 'add' and (tender.status != 'active.enquiries' or tender.enquiryPeriod.startDate and get_now() < tender.enquiryPeriod.startDate or get_now() > tender.enquiryPeriod.endDate):
            self.request.errors.add('body', 'data', 'Can add question only in enquiryPeriod')
            self.request.errors.status = 403
            return
        if operation == 'update' and tender.status != 'active.enquiries':
            self.request.errors.add('body', 'data', 'Can\'t update question in current ({}) tender status'.format(tender.status))
            self.request.errors.status = 403
            return
        question = self.request.validated['question']
        items_dict = {i.id: i.relatedLot for i in tender.items}
        if any([
            i.status != 'active'
            for i in tender.lots
            if question.questionOf == 'lot' and i.id == question.relatedItem or question.questionOf == 'item' and i.id == items_dict[question.questionOf]
        ]):
            self.request.errors.add('body', 'data', 'Can {} question only in active lot status'.format(operation))
            self.request.errors.status = 403
            return
        return True

    @json_view(content_type="application/json", validators=(validate_question_data,), permission='create_question')
    def collection_post(self):
        """Post a question
        """
        if not self.validate_question('add'):
            return
        question = self.request.validated['question']
        self.request.context.questions.append(question)
        if save_tender(self.request):
            self.LOGGER.info('Created tender question {}'.format(question.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_question_create'}, {'question_id': question.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Tender Questions', tender_id=self.request.context.id, question_id=question.id)
            return {'data': question.serialize("view")}

    @json_view(permission='view_tender')
    def collection_get(self):
        """List questions
        """
        return {'data': [i.serialize(self.request.validated['tender'].status) for i in self.request.validated['tender'].questions]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the question
        """
        return {'data': self.request.validated['question'].serialize(self.request.validated['tender'].status)}

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_patch_question_data,))
    def patch(self):
        """Post an Answer
        """
        if not self.validate_question('update'):
            return
        self.context.dateAnswered = get_now()
        if apply_patch(self.request, src=self.request.context.serialize()):
            self.LOGGER.info('Updated tender question {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_question_patch'}))
            return {'data': self.request.context.serialize(self.request.validated['tender_status'])}
