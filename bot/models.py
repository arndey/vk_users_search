from django.db import models  # Create your models here.


class UserData(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True,
                          serialize=False, verbose_name='id')
    date = models.DateTimeField(auto_now_add=True,
                                verbose_name='date_created')
    user_id = models.IntegerField('user_id')
    suitable = models.BooleanField('suitable')

    def save(self, *args, **kwargs):
        super(UserData, self).save(*args, **kwargs)
