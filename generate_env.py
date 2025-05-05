import secrets
import sys
import os

# Function to generate a secure password
def generate_secure_password(length=16):
    return secrets.token_urlsafe(length)

# Function to copy and modify the environment file
def create_env_file(env_type):
    if env_type not in ['dev', 'prod']:
        raise ValueError("env_type must be 'dev' or 'prod'")

    source_file = '.env.sample'
    target_file = f'.env.{env_type}'

    if os.path.exists(target_file):
        print(f"Error: Target file '{target_file}' already exists.")
        sys.exit(1)

    # Read the contents of the target file
    with open(source_file, 'r') as file:
        content = file.readlines()

    # Replace placeholders with secure passwords
    replacements = {
        'POSTGRES_PASSWORD=': f'POSTGRES_PASSWORD={generate_secure_password(32)}',
        'DJANGO_SECRET_KEY=': f'DJANGO_SECRET_KEY={generate_secure_password(32)}',
        'DJANGO_DB_PASSWORD=': f'DJANGO_DB_PASSWORD={generate_secure_password(32)}',
    }

    # Modify the content
    new_content = []
    for line in content:
        for key, value in replacements.items():
            if line.startswith(key):
                line = f'{key}{value}\n'

        new_content.append(line)

    # Write the modified content back to the target file
    with open(target_file, 'w') as file:
        file.writelines(new_content)

    print(f"Environment file '{target_file}' created with secure passwords.")

# Main method to handle command line arguments
def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_env.py [dev|prod]")
        sys.exit(1)

    env_type = sys.argv[1]
    if env_type not in ['dev', 'prod']:
        print("Error: Argument must be 'dev' or 'prod'")
        sys.exit(1)

    create_env_file(env_type)

if __name__ == "__main__":
    main()
