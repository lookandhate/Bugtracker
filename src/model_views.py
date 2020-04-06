from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for


# MyModelView for admin panel
class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.is_admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('access_restricted', from_page='admin', message='Test', code='403'))


# AdminIndexView for admin panel
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.is_admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('access_restricted', from_page='admin', message='Test', code='403'))
