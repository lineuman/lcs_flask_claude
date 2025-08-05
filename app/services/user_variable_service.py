from app.models import db, UserVariables
from typing import Optional, List


class UserVariableService:
    @staticmethod
    def create_variable(user_id: int, variable_name: str, variable_value: str) -> Optional[UserVariables]:
        """
        Create a user variable
        
        Args:
            user_id: User ID
            variable_name: Variable name
            variable_value: Variable value
        
        Returns:
            UserVariables object or None (if variable already exists)
        """
        # Check if a variable with the same name already exists
        existing_variable = UserVariableService.get_variable_by_name(user_id, variable_name)
        if existing_variable:
            return None
        
        new_variable = UserVariables(
            user_id=user_id,
            variable_name=variable_name,
            variable_value=variable_value
        )
        db.session.add(new_variable)
        db.session.commit()
        return new_variable
    
    @staticmethod
    def get_variable_by_id(variable_id: int) -> Optional[UserVariables]:
        """
        Get user variable by ID
        
        Args:
            variable_id: Variable ID
            
        Returns:
            UserVariables object or None
        """
        return UserVariables.query.get(variable_id)
    
    @staticmethod
    def get_variable_by_name(user_id: int, variable_name: str) -> Optional[UserVariables]:
        """
        Get user variable by user ID and variable name
        
        Args:
            user_id: User ID
            variable_name: Variable name
            
        Returns:
            UserVariables object or None
        """
        return UserVariables.query.filter_by(user_id=user_id, variable_name=variable_name).first()
    
    @staticmethod
    def get_user_variables(user_id: int) -> List[UserVariables]:
        """
        Get all variables for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of UserVariables objects
        """
        return UserVariables.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def update_variable(variable_id: int, variable_value: str) -> Optional[UserVariables]:
        """
        Update user variable value
        
        Args:
            variable_id: Variable ID
            variable_value: New variable value
            
        Returns:
            Updated UserVariables object or None (if variable doesn't exist)
        """
        variable = UserVariableService.get_variable_by_id(variable_id)
        if not variable:
            return None
        
        variable.variable_value = variable_value
        db.session.commit()
        return variable
    
    @staticmethod
    def delete_variable(variable_id: int) -> bool:
        """
        Delete user variable
        
        Args:
            variable_id: Variable ID
            
        Returns:
            Whether deletion was successful
        """
        variable = UserVariableService.get_variable_by_id(variable_id)
        if not variable:
            return False
        
        db.session.delete(variable)
        db.session.commit()
        return True
    
    @staticmethod
    def delete_variable_by_name(user_id: int, variable_name: str) -> bool:
        """
        Delete user variable by user ID and variable name
        
        Args:
            user_id: User ID
            variable_name: Variable name
            
        Returns:
            Whether deletion was successful
        """
        variable = UserVariableService.get_variable_by_name(user_id, variable_name)
        if not variable:
            return False
        
        db.session.delete(variable)
        db.session.commit()
        return True