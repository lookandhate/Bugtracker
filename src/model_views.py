""" There are some classes for flask-admin """

from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for


# MyModelView for admin panel
class MyModelView(ModelView):
    """
    This is class that implements model views on /admin page
    It inherits from basic flask_admin.contrib.sqla.ModelView class
    And here I'am overwriting some methods of parent class
    """

    def is_accessible(self):
        """
        This method checks does current_user have access to Model views on /admin page
        BUT, this method restricts access only to model views
        In other words user still has access to /admin but can't go to model views
        For limiting access for /admin page too we need to overwrite AdminIndexView too

        :return:bool: True if user has access(i.e User is admin) and False if user doesn't
        """
        if current_user.is_authenticated:
            return current_user.is_admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        """
        This method implements politics for inaccessible request to Model views on  /admin page
        """
        return redirect(url_for('access_restricted'))


# AdminIndexView for admin panel
class MyAdminIndexView(AdminIndexView):
    """
    This is class that implements /admin page
    It inherits from basic flask_admin.AdminIndexView
    And here I'am overwriting some methods of parent class
    """

    def is_accessible(self):
        """
        This method checks does current_user have access to /admin page
        :return:bool: True if user has access(i.e User is admin) and False if user doesn't
        """
        if current_user.is_authenticated:
            return current_user.is_admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        """
        This method implements politics for inaccessible request to /admin page
        """
        return redirect(url_for('access_restricted'))
