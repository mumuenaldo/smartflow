from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import Document, Comment, User, Department, LearnMoreContent, FAQ


# ─────────────────────────────────────────────
# LOGIN FORM
# ─────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )


# ─────────────────────────────────────────────
# BASE REGISTRATION FORM (Shared fields)
# ─────────────────────────────────────────────
class BaseRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password', 'confirm_password', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username


# ─────────────────────────────────────────────
# STUDENT REGISTRATION FORM
# ─────────────────────────────────────────────
class StudentRegistrationForm(BaseRegistrationForm):
    student_id = forms.CharField(
        label='Student ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., T2420016'}),
        required=True,
    )
    phone_number = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0771234567'}),
        required=False,
    )
    address = forms.CharField(
        label='Address',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your address'}),
        required=False,
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ['student_id', 'phone_number', 'address']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.student_id = self.cleaned_data.get('student_id')
        user.phone_number = self.cleaned_data.get('phone_number')
        user.address = self.cleaned_data.get('address')
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# REGISTRY CLERK REGISTRATION FORM
# ─────────────────────────────────────────────
class ClerkRegistrationForm(BaseRegistrationForm):
    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'clerk'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# STAFF MEMBER REGISTRATION FORM
# ─────────────────────────────────────────────
class StaffRegistrationForm(BaseRegistrationForm):
    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# SUPERVISOR REGISTRATION FORM
# ─────────────────────────────────────────────
class SupervisorRegistrationForm(BaseRegistrationForm):
    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'supervisor'
        user.is_staff = True
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# ADMINISTRATOR REGISTRATION FORM
# ─────────────────────────────────────────────
class AdminRegistrationForm(BaseRegistrationForm):
    admin_key = forms.CharField(
        label='Admin Registration Key',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter admin key'}),
        required=True,
        help_text='Required for admin registration'
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ['admin_key']

    def clean_admin_key(self):
        admin_key = self.cleaned_data.get('admin_key')
        if admin_key != 'SMARTFLOW_ADMIN_2024':
            raise ValidationError("Invalid admin registration key.")
        return admin_key

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# DOCUMENT FORM (UPDATED WITH PRIORITY)
# ─────────────────────────────────────────────
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'document_type', 
            'department', 'priority', 'file_path', 'requires_approval'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your request...'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),  # NEW
            'file_path': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        self.fields['department'].empty_label = "Select Department"
        self.fields['department'].required = True
        self.fields['description'].required = False

# ─────────────────────────────────────────────
# DOCUMENT ASSIGNMENT FORM
# ─────────────────────────────────────────────
class AssignDocumentForm(forms.Form):
    assign_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).exclude(role__in=['admin', 'student']),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Assign To',
        empty_label="Select user"
    )
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        label='Due Date (optional)'
    )


# ─────────────────────────────────────────────
# APPROVAL / REJECTION FORM (Supervisor)
# ─────────────────────────────────────────────
class ApprovalForm(forms.Form):
    ACTION_CHOICES = [
        ('approved', '✅ Approve'),
        ('rejected', '❌ Reject'),
        ('in_review', '🔄 Return for Correction'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Decision'
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Supervisor comments / notes…',
        }),
        label='Comments / Notes'
    )


# ─────────────────────────────────────────────
# COMMENT FORM
# ─────────────────────────────────────────────
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Add a comment…',
            })
        }


# ─────────────────────────────────────────────
# USER CREATION FORM (Admin)
# ─────────────────────────────────────────────
class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'department', 'student_id', 'phone_number', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# DEPARTMENT FORM (Admin)
# ─────────────────────────────────────────────
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['dept_name', 'description', 'location']
        widgets = {
            'dept_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Department description'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office location'}),
        }


# ─────────────────────────────────────────────
# PROFILE UPDATE FORM (For Students)
# ─────────────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0771234567'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ─────────────────────────────────────────────
# LEARN MORE CONTENT FORM (Admin)
# ─────────────────────────────────────────────
class LearnMoreContentForm(forms.ModelForm):
    class Meta:
        model = LearnMoreContent
        fields = ['section_title', 'content', 'order', 'is_active']
        widgets = {
            'section_title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ─────────────────────────────────────────────
# FAQ FORM (Admin)
# ─────────────────────────────────────────────
class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order', 'is_active']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ─────────────────────────────────────────────
# BULK UPLOAD FORM
# ─────────────────────────────────────────────
class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text='Upload CSV with columns: title, description, document_type, department'
    )