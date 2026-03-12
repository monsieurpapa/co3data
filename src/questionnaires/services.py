from .models import Submission, Answer

class QuestionnaireService:
    """Service for handling questionnaire submissions."""

    @staticmethod
    def submit_answers(questionnaire, user, target_object, answers_data):
        """
        Processes a questionnaire submission.
        answers_data: list of dicts like {'question_id': 1, 'value': 'some text' or 123}
        """
        submission = Submission.objects.create(
            questionnaire=questionnaire,
            submitted_by=user,
            content_object=target_object
        )
        
        for ans in answers_data:
            question = questionnaire.questions.get(id=ans['question_id'])
            answer_obj = Answer(submission=submission, question=question)
            
            # Map values based on question type
            if question.question_type == 'number':
                answer_obj.value_number = ans['value']
            elif question.question_type == 'date':
                answer_obj.value_date = ans['value']
            elif question.question_type == 'boolean':
                answer_obj.value_boolean = ans['value']
            else:
                answer_obj.value_text = str(ans['value'])
            
            answer_obj.save()
            
        return submission
