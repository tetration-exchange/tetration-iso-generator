from flask import Flask, render_template, flash, request, send_file
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import Form, TextField, validators
from werkzeug.utils import secure_filename
import tempfile
import shutil
import os
import subprocess

application = Flask(__name__)
application.config.from_object(__name__)
application.config['SECRET_KEY'] = 'TETRATION_IS_AWESOME'


class UploadForm(FlaskForm):
    ip1 = TextField(
        'Interface 1 IP Address (CIDR format)',
        validators=[validators.required()],
    )
    ip2 = TextField(
        'Interface 2 IP Address (CIDR format)',
        validators=[validators.required()],
    )
    ip3 = TextField(
        'Interface 3 IP Address (CIDR format)',
        validators=[validators.required()],
    )

    gw1 = TextField('Interface 1 Gateway IP', validators=[validators.required()])
    gw2 = TextField('Interface 2 Gateway IP', validators=[validators.required()])
    gw3 = TextField('Interface 3 Gateway IP', validators=[validators.required()])

    hostname = TextField('Hostname (optional):')
    proxy = TextField('HTTPS Proxy (optional):')
    dns = TextField('DNS (required for TaaS):')
    key = TextField('Activation Key (required for TaaS):')

    rpm = FileField('Appliance RPM:', validators=[FileRequired()])

    anyconnect = FileField('tet-anyconnect-user.conf:', validators=[])
    enforcer = FileField('tnp-enforcer.conf:', validators=[])
    aws_cred = FileField('aws_cred.csv:', validators=[])
    aws_s3_bucket_list = FileField('aws_s3_bucket_list.conf:', validators=[])


@application.route("/", methods=['GET', 'POST'])
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        print "Creating ISO"
        iso = create_iso(form)
        return send_file(iso, as_attachment=True)

    flash_errors(form)

    return render_template('form.html', form=form)


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (getattr(form, field).label.text, error))


def create_iso(form):
    dirpath = tempfile.mkdtemp()
    print "created temp dir", dirpath
    iso_file = os.path.join(dirpath, 'tetration-appliance-ova-config.iso')
    iso_folder = os.path.join(dirpath, 'iso')
    os.mkdir(iso_folder)

    f = form.rpm.data
    filename = secure_filename(f.filename)
    f.save(os.path.join(iso_folder, filename))

    with open(os.path.join(iso_folder, 'ip_config'), 'w') as ip_config:
        ip_config.write("{} {}\n".format(form.ip1.data, form.gw1.data))
        ip_config.write("{} {}\n".format(form.ip2.data, form.gw2.data))
        ip_config.write("{} {}".format(form.ip3.data, form.gw3.data))

    if form.hostname.data:
        with open(os.path.join(iso_folder, 'host_name'), 'w') as host_name:
            host_name.write(form.hostname.data)

    if form.dns.data:
        with open(os.path.join(iso_folder, 'resolv.conf'), 'w') as resolv:
            resolv.write(form.dns.data)

    if form.proxy.data or form.key.data:
        with open(os.path.join(iso_folder, 'user.cfg'), 'w') as user_cfg:
            user_cfg.write("HTTPS_PROXY={}\n".format(form.proxy.data))
            user_cfg.write("ACTIVATION_KEY={}\n".format(form.key.data))

    optional_files = {
        'tet-anyconnect-user.cfg': form.anyconnect,
        'tnp-enforcer.conf': form.enforcer,
        'aws_cred.csv': form.aws_cred,
        'aws_s3_bucket_list.conf': form.aws_s3_bucket_list
    }

    for filename, filefield in optional_files.items():
        f = filefield.data
        if f:
            f.save(os.path.join(iso_folder, filename))

    subprocess.call(['mkisofs', '-r', '-o', iso_file, iso_folder])

    return iso_file
    # shutil.rmtree(dirpath)


if __name__ == "__main__":
    application.run()