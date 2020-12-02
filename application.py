from flask import Flask, render_template, flash, request, send_file
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from validators import FileSize
from wtforms import TextField, validators
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
    ip2 = TextField('Interface 2 IP Address (CIDR format)')
    ip3 = TextField('Interface 3 IP Address (CIDR format)')

    gw1 = TextField('Interface 1 Gateway IP', validators=[validators.required()])
    gw2 = TextField('Interface 2 Gateway IP', validators=[])
    gw3 = TextField('Interface 3 Gateway IP', validators=[])

    hostname = TextField('Hostname (optional):')
    proxy = TextField('HTTPS Proxy (optional):')
    dns_1 = TextField('DNS Nameserver 1 (required for TaaS):')
    dns_2 = TextField('DNS Nameserver 2 (required for TaaS):')
    dns_domain = TextField('DNS Search Domain (required for TaaS):')
    key = TextField('Activation Key (required for TaaS):')

    rpm = FileField('Appliance RPM (or .tar.gz for TAN):', validators=[FileRequired(), FileSize(20971520, 0, message="may not be larger than 20MB")])

    anyconnect = FileField('tet-anyconnect.conf:', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])
    anyconnect_user = FileField('tet-anyconnect-user.conf:', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])
    anyconnect_ldap = FileField('ldap.cert', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])
    enforcer = FileField('tnp-enforcer.conf:', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])
    aws_cred = FileField('aws_cred.csv:', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])
    aws_s3_bucket_list = FileField('aws_s3_bucket_list.conf:', validators=[FileSize(1000000, 0, message="may not be larger than 1MB")])


@application.route("/eula", methods=['GET'])
def eula():
    return render_template('eula.html')


@application.route("/", methods=['GET', 'POST'])
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        print("Creating ISO")
        iso = create_iso(form)
        return send_file(iso, as_attachment=True)

    flash_errors(form)

    return render_template('form.html', form=form)


def flash_errors(form):
    for field, errors in list(form.errors.items()):
        for error in errors:
            flash("Error in the %s field - %s" % (getattr(form, field).label.text, error))


def create_iso(form):
    dirpath = tempfile.mkdtemp()
    print("created temp dir", dirpath)
    iso_file = os.path.join(dirpath, 'tetration-appliance-ova-config.iso')
    iso_folder = os.path.join(dirpath, 'iso')
    os.mkdir(iso_folder)

    f = form.rpm.data
    filename = secure_filename(f.filename)
    f.save(os.path.join(iso_folder, filename))

    with open(os.path.join(iso_folder, 'ip_config'), 'w') as ip_config:
        ip_config.write("{} {}\n".format(form.ip1.data, form.gw1.data))
        ip_config.write("{} {}\n".format(form.ip2.data, form.gw2.data))
        ip_config.write("{} {}\n".format(form.ip3.data, form.gw3.data))

    if form.hostname.data:
        with open(os.path.join(iso_folder, 'host_name'), 'w') as host_name:
            host_name.write(form.hostname.data)

    if form.dns_1.data:
        with open(os.path.join(iso_folder, 'resolv.conf'), 'w') as resolv:
            resolv.write("nameserver {}\n".format(form.dns_1.data))
            if form.dns_1.data:
                resolv.write("nameserver {}\n".format(form.dns_2.data))
            if form.dns_domain.data:
                resolv.write("search {}".format(form.dns_domain.data))

    if form.proxy.data or form.key.data:
        with open(os.path.join(iso_folder, 'user.cfg'), 'w') as user_cfg:
            if form.proxy.data:
                user_cfg.write("HTTPS_PROXY={}\n".format(form.proxy.data))
            if form.key.data:
                user_cfg.write("ACTIVATION_KEY={}\n".format(form.key.data))

    optional_files = {
        'tet-anyconnect.conf': form.anyconnect,
        'tet-anyconnect-user.conf': form.anyconnect_user,
        'ldap.cert': form.anyconnect_ldap,
        'tnp-enforcer.conf': form.enforcer,
        'aws_cred.csv': form.aws_cred,
        'aws_s3_bucket_list.conf': form.aws_s3_bucket_list
    }

    for filename, filefield in list(optional_files.items()):
        f = filefield.data
        if f:
            f.save(os.path.join(iso_folder, filename))

    subprocess.call(['mkisofs', '-r', '-o', iso_file, iso_folder])

    return iso_file


if __name__ == "__main__":
    application.run()