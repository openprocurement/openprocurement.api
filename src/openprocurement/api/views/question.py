# -*- coding: utf-8 -*-
from cornice.resource import resource, view
from openprocurement.api.models import Question, Revision
from openprocurement.api.utils import (
    apply_data_patch,
    filter_data,
    get_revision_changes,
)
from openprocurement.api.validation import (
    validate_question_data,
    validate_patch_question_data,
    validate_tender_question_exists,
    validate_tender_exists_by_tender_id,
)


@resource(name='Tender Questions',
          collection_path='/tenders/{tender_id}/questions',
          path='/tenders/{tender_id}/questions/{id}',
          description="Tender questions")
class TenderQuestionResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @view(content_type="application/json", validators=(validate_question_data, validate_tender_exists_by_tender_id), renderer='json')
    def collection_post(self):
        """Post a question
        """
        tender = self.request.validated['tender']
        question_data = filter_data(self.request.validated['data'])
        question = Question(question_data)
        src = tender.serialize("plain")
        tender.questions.append(question)
        patch = get_revision_changes(tender.serialize("plain"), src)
        tender.revisions.append(Revision({'changes': patch}))
        try:
            tender.store(self.db)
        except Exception, e:
            return self.request.errors.add('body', 'data', str(e))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Tender Questions', tender_id=tender.id, id=question['id'])
        return {'data': question.serialize("view")}

    @view(renderer='json', validators=(validate_tender_exists_by_tender_id,))
    def collection_get(self):
        """List questions
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].questions]}

    @view(renderer='json', validators=(validate_tender_question_exists,))
    def get(self):
        """Retrieving the question
        """
        return {'data': self.request.validated['question'].serialize("view")}

    @view(content_type="application/json", validators=(validate_patch_question_data, validate_tender_question_exists), renderer='json')
    def patch(self):
        """Post an Answer
        """
        tender = self.request.validated['tender']
        question = self.request.validated['question']
        question_data = filter_data(self.request.validated['data'])
        if question_data:
            src = tender.serialize("plain")
            question.import_data(apply_data_patch(question.serialize(), question_data))
            patch = get_revision_changes(tender.serialize("plain"), src)
            if patch:
                tender.revisions.append(Revision({'changes': patch}))
                try:
                    tender.store(self.db)
                except Exception, e:
                    return self.request.errors.add('body', 'data', str(e))
        return {'data': question.serialize("view")}
