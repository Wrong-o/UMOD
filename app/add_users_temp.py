from database import get_db  # Import the database session dependency
from fastapi import FastAPI, HTTPException, status
from models import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

app = FastAPI()

def create_user(email: str, password: str, db: Session):
    """
    Creates a new user in the database.

    Args:
        email (str): The email of the new user.
        password (str): The password for the new user.
        db (Session): The database session.

    Raises:
        HTTPException: If the user already exists or another error occurs.
    """
    try:
        user = User(email=email)
        user.set_password(password)  # Hash and set the password
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User {email} created successfully!")
        return {"status": "success", "user_id": user.user_id, "email": user.email}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )

# Example usage
if __name__ == "__main__":
    # Instantiate the database session manually
    db_session = next(get_db())  # Get the session from get_db

    # Call create_user with the database session
    try:
        result = create_user("samuel@test.se", "testpassword", db_session)
        print(result)
    except HTTPException as e:
        print(f"Error: {e.detail}")
    finally:
        db_session.close()  # Ensure the session is properly closed




"christoffer@test.se", "testpassword"