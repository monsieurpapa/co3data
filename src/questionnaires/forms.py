from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Submission, Answer, Question

class QuestionnaireSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.questionnaire = kwargs.pop('questionnaire')
        super().__init__(*args, **kwargs)
        
        for question in self.questionnaire.questions.all():
            field_name = f'question_{question.id}'
            field_label = question.text
            required = question.is_required
            
            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=field_label, required=required, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
                )
            elif question.question_type == 'number':
                self.fields[field_name] = forms.DecimalField(
                    label=field_label, required=required, widget=forms.NumberInput(attrs={'class': 'form-control'})
                )
            elif question.question_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=field_label, required=required, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                )
            elif question.question_type == 'boolean':
                self.fields[field_name] = forms.BooleanField(
                    label=field_label, required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
            elif question.question_type == 'select':
                choices = [(opt, opt) for opt in (question.options or [])]
                self.fields[field_name] = forms.ChoiceField(
                    label=field_label, required=required, choices=choices, widget=forms.Select(attrs={'class': 'form-select'})
                )
            # Add more types as needed

    def save(self, submission):
        for question in self.questionnaire.questions.all():
            field_name = f'question_{question.id}'
            value = self.cleaned_data.get(field_name)
            
            answer_data = {
                'submission': submission,
                'question': question,
            }
            
            if question.question_type == 'text':
                answer_data['value_text'] = value
            elif question.question_type == 'number':
                answer_data['value_number'] = value
            elif question.question_type == 'date':
                answer_data['value_date'] = value
            elif question.question_type == 'boolean':
                answer_data['value_boolean'] = value
            elif question.question_type == 'select':
                answer_data['value_text'] = value
                
            Answer.objects.create(**answer_data)
