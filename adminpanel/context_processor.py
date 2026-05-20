from .admin_config import ADMIN_MODULES

def admin_modules(request):
    return {'ADMIN_MODULES': ADMIN_MODULES}
