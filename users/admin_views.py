from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView as DjangoAdminLoginView

class AdminLoginView(DjangoAdminLoginView):
    template_name = 'admin/login.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_staff:
            self.request.session.save()
            response.set_cookie(
                'admin_sessionid',
                self.request.session.session_key,
                path='/admin/',
                httponly=True
            )
        return response