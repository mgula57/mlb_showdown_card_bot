"""
Lambda handler for refreshing the Card of the Day.
Scheduled to run daily at 8:00 AM EDT.
"""
import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import mlb_showdown_bot package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mlb_showdown_bot.core.database.postgres_db import PostgresDB


def handler(event, context):
    """
    Lambda handler that refreshes the Card of the Day.
    
    Args:
        event: Lambda event object (from EventBridge scheduled event)
        context: Lambda context object
    
    Returns:
        dict: Response with status code and message
    """
    
    print(f"Card of the Day refresh triggered at {datetime.now().isoformat()}")
    
    try:
        # Initialize database connection
        db = PostgresDB()
        
        # Check if connection is established
        if db.connection is None:
            error_msg = "Failed to establish database connection"
            print(f"ERROR: {error_msg}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': error_msg
                })
            }
        
        # Refresh card of the day
        print("Refreshing Card of the Day...")
        db.refresh_card_of_the_day()
        
        success_msg = f"Card of the Day successfully refreshed at {datetime.now().isoformat()}"
        print(success_msg)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': success_msg,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        error_msg = f"Error refreshing Card of the Day: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
        }
    
    finally:
        # Close database connection
        if 'db' in locals() and db.connection:
            db.connection.close()
            print("Database connection closed")
