from django import forms
from .models import Member, Cooperative

class CooperativeForm(forms.ModelForm):
    class Meta:
        model = Cooperative
        fields = ['name', 'registration_number', 'type', 'establishment_date', 'contact_person', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'establishment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_person': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'cooperative', 'first_name', 'last_name', 'member_id', 
            'gender', 'age_group', 'phone_number', 
            'territory', 'groupement', 'village',
            'is_marginalized', 'is_board_member', 'board_role'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'member_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Member ID'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'territory': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Territory'}),
            'groupement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Groupement'}),
            'village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}),
            'board_role': forms.Select(attrs={'class': 'form-select'}),
            'cooperative': forms.Select(attrs={'class': 'form-select'}),
            'is_marginalized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_board_member': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_board_member = cleaned_data.get('is_board_member')
        board_role = cleaned_data.get('board_role')

        if is_board_member and not board_role:
            self.add_error('board_role', "Board role is required for board members.")
        
        return cleaned_data
