from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, BooleanField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class DocumentUploadForm(FlaskForm):
    """Form for uploading image/PDF files and selecting scanner configuration."""
    document = FileField(
        'Select Document or Image',
        validators=[
            FileRequired(message="Please select a file to upload."),
            FileAllowed(['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'pdf'], 'Only JPG, PNG, BMP, TIFF, and PDF files are allowed!')
        ]
    )
    
    language = SelectField(
        'OCR Language',
        choices=[
            ('eng+hin', 'English + Hindi (Multilingual / द्विभाषी)'),
            ('eng', 'English'),
            ('hin', 'Hindi (हिन्दी)'),
            ('spa', 'Spanish'),
            ('fra', 'French'),
            ('deu', 'German'),
            ('ita', 'Italian'),
            ('por', 'Portuguese'),
            ('rus', 'Russian'),
            ('chi_sim', 'Chinese (Simplified)')
        ],
        default='eng+hin'
    )
    
    enhancement_mode = SelectField(
        'Enhancement Mode',
        choices=[
            ('color', 'Original / Same as Image (Enhanced Readable)'),
            ('adaptive', 'Adaptive Threshold (Clean Black & White)'),
            ('grayscale', 'Grayscale High-Contrast'),
            ('otsu', 'Otsu Binarization'),
            ('none', 'Unmodified Original (Raw Upload)')
        ],
        default='color'
    )
    
    auto_rotate = BooleanField('Auto-Rotate / Deskew', default=True)
    sharpen = BooleanField('Apply Sharpening Filter', default=True)
    noise_reduction = BooleanField('Apply Noise Reduction', default=False)
    
    submit = SubmitField('Scan & Process Document')


class ContactForm(FlaskForm):
    """Form for user contact and feedback."""
    name = StringField(
        'Full Name',
        validators=[DataRequired(message="Name is required."), Length(min=2, max=50)]
    )
    email = StringField(
        'Email Address',
        validators=[DataRequired(message="Email is required."), Email(message="Please enter a valid email address.")]
    )
    subject = StringField(
        'Subject',
        validators=[DataRequired(message="Subject is required."), Length(min=3, max=100)]
    )
    message = TextAreaField(
        'Message',
        validators=[DataRequired(message="Message content is required."), Length(min=10, max=2000)]
    )
    submit = SubmitField('Send Message')
