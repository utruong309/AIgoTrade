import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('symbol', models.CharField(db_index=True, max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('exchange', models.CharField(max_length=20)),
                ('sector', models.CharField(blank=True, max_length=50, null=True)),
                ('industry', models.CharField(blank=True, max_length=100, null=True)),
                ('market_cap', models.BigIntegerField(blank=True, null=True)),
                ('current_price', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('previous_close', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('day_change', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('day_change_percent', models.DecimalField(decimal_places=4, default=0, max_digits=8)),
                ('volume', models.BigIntegerField(default=0)),
                ('avg_volume', models.BigIntegerField(default=0)),
                ('pe_ratio', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('dividend_yield', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_price_update', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'trading_stocks',
                'ordering': ['symbol'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('risk_tolerance', models.CharField(choices=[('conservative', 'Conservative'), ('moderate', 'Moderate'), ('aggressive', 'Aggressive')], default='moderate', max_length=20)),
                ('investment_experience', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=20)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'trading_users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('total_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('cash_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('invested_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_return', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_return_percent', models.DecimalField(decimal_places=4, default=0, max_digits=8)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolios', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'trading_portfolios',
                'ordering': ['-is_default', '-created_at'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_type', models.CharField(choices=[('buy', 'Buy'), ('sell', 'Sell'), ('dividend', 'Dividend'), ('deposit', 'Cash Deposit'), ('withdrawal', 'Cash Withdrawal'), ('fee', 'Fee')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('executed', 'Executed'), ('cancelled', 'Cancelled'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('quantity', models.DecimalField(decimal_places=6, default=0, max_digits=15)),
                ('price', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fees', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('transaction_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='trading.portfolio')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='trading.stock')),
            ],
            options={
                'db_table': 'trading_transactions',
                'ordering': ['-transaction_date'],
            },
        ),
        migrations.CreateModel(
            name='Holding',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity', models.DecimalField(decimal_places=6, default=0, max_digits=15)),
                ('average_cost', models.DecimalField(decimal_places=4, default=0, max_digits=15)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('current_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('unrealized_gain_loss', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('unrealized_gain_loss_percent', models.DecimalField(decimal_places=4, default=0, max_digits=8)),
                ('first_purchase_date', models.DateTimeField()),
                ('last_transaction_date', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holdings', to='trading.portfolio')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holdings', to='trading.stock')),
            ],
            options={
                'db_table': 'trading_holdings',
                'ordering': ['-current_value'],
                'unique_together': {('portfolio', 'stock')},
            },
        ),
    ]