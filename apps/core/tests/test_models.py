import pytest
from apps.core.models import SystemConfig


@pytest.mark.django_db
def test_system_config_singleton():
    # Initially none exists
    assert SystemConfig.objects.count() == 0
    
    # Get creates one
    config = SystemConfig.get()
    assert SystemConfig.objects.count() == 1
    assert config.pk == 1
    assert config.save_emails_to_sent_folder is False
    
    # Getting again returns the same one
    config2 = SystemConfig.get()
    assert config2.pk == config.pk
    assert SystemConfig.objects.count() == 1
    
    # Saving always uses pk=1
    config2.pk = 99
    config2.save()
    assert SystemConfig.objects.count() == 1
    assert SystemConfig.objects.get().pk == 1
