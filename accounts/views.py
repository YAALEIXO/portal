from django.contrib.auth.views import LoginView, LogoutView


class PortalLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get("lembrar"):
            self.request.session.set_expiry(0)
        return response


class PortalLogoutView(LogoutView):
    pass
