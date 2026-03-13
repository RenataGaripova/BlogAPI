SUPERUSER_NAME="admin_user"
SUPERUSER_EMAIL="admin@gmail.com"
SUPERUSER_PASS="12345"
SUPERUSER_FIRST_NAME="admin"
SUPERUSER_LAST_NAME="admin"

ENV_FILE="../settings/.env"

VENV_FOLDER="../venv"
# Check .env file
if [ ! -d "../settings" ]; then 
    echo "The settings folder does not exist."
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then 
    echo "The .env file does not exist."
    exit 1
fi
set -a
. "$ENV_FILE"
set +a

VARS="
PROJECT_ENV_ID
DJANGO_SECRET_KEY
"
for VAR in $VARS; do
    var_value=$(eval echo \$$VAR)
    if [ -z "$var_value" ]; then
        echo "$VAR is unset. Please set it and run this script again."
        exit 1
    fi
done
echo "All .env variables are set."

# Create VENV
if [ ! -d "$VENV_FOLDER" ]; then
    python3 -m venv "$VENV_FOLDER"
    echo "Venv was successfuly created."
else
    echo "Venv already exists."
fi
source "$VENV_FOLDER/bin/activate"
# Install dependencies
if [ ! -d "../requirements" ]; then 
    echo "The requirements folder does not exist."
    exit 1
fi
REQUIREMENTS_FILE="../requirements/base.py"
if [ ! -f "$REQUIREMENTS_FILE" ]; then 
    echo "The requirements/base.py file does not exist."
    exit 1
fi
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"
# Apply migrations
python ../manage.py migrate --noinput
# Collect static
python ../manage.py collectstatic --noinput
# Compile translations
python ../manage.py compilemessages
# Create superuser
cat <<EOF | python3 manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email="$SUPERUSER_EMAIL").exists():
    superuser=User.objects.create(
        username="$SUPERUSER_NAME",
        email="$SUPERUSER_EMAIL",
        first_name="$SUPERUSER_FIRST_NAME",
        last_name="$SUPERUSER_LAST_NAME",
        password="$SUPERUSER_PASS"
    )
    superuser.set_password("$SUPERUSER_PASS")
    superuser.save()
    print('Superuser created successfully')
else:
    print('Superuser already exists, skipping creation')
EOF
# Generate test data
python ../manage.py fake
# Start the server
python ../manage.py runserver