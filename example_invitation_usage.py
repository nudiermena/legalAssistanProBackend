#!/usr/bin/env python3
"""
Example usage of the invitation endpoint
"""

import requests
import json
from datetime import datetime, timedelta

def example_send_invitation():
    """Example of how to send an invitation"""
    
    # Base URL for your API
    base_url = "http://localhost:8000"
    
    # Example invitation data
    invitation_data = {
        "friendName": "Carlos Rodríguez",
        "inviterName": "Ana Martínez",
        "inviteCode": "FRIEND2025",
        "shareUrl": "https://app.miasistentelegalia.com/friend-invite/FRIEND2025",
        "dailyLimit": 10,
        "trialDays": 7,
        "expiresAt": "15 de septiembre de 2025",
        "friendEmail": "carlos.rodriguez@example.com"
    }
    
    print("=== Example: Sending Friend Invitation ===\n")
    print("Invitation Data:")
    print(json.dumps(invitation_data, indent=2))
    print("\n" + "="*50 + "\n")
    
    try:
        # Send the invitation
        response = requests.post(
            f"{base_url}/invitation/send",
            json=invitation_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Invitation sent successfully!")
            print(f"Message: {result['message']}")
            print(f"Email ID: {result['email_id']}")
        else:
            print("❌ Failed to send invitation")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def example_health_check():
    """Example of how to check the service health"""
    
    base_url = "http://localhost:8000"
    
    print("=== Example: Health Check ===\n")
    
    try:
        response = requests.get(f"{base_url}/invitation/health")
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Service is healthy!")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"Timestamp: {result['timestamp']}")
        else:
            print("❌ Service health check failed")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def example_frontend_integration():
    """Example of how the frontend would integrate with this endpoint"""
    
    print("=== Example: Frontend Integration ===\n")
    
    # This is how the frontend would call the API
    frontend_code = '''
// Frontend JavaScript example
const sendFriendInvitation = async (formData) => {
  const invitationData = {
    friendName: formData.friendName,
    inviterName: currentUser.name,
    inviteCode: generateInviteCode(),
    shareUrl: `${window.location.origin}/friend-invite/${inviteCode}`,
    dailyLimit: parseInt(formData.dailyLimit),
    trialDays: parseInt(formData.trialDays),
    expiresAt: calculateExpirationDate(formData.trialDays),
    friendEmail: formData.friendEmail
  };

  try {
    const response = await fetch('/invitation/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}`
      },
      body: JSON.stringify(invitationData)
    });

    const result = await response.json();

    if (response.ok) {
      showSuccessMessage('¡Invitación enviada exitosamente!');
      closeInvitationModal();
    } else {
      showErrorMessage('Error al enviar la invitación: ' + result.detail);
    }
  } catch (error) {
    showErrorMessage('Error de conexión: ' + error.message);
  }
};
'''
    
    print("Frontend JavaScript code:")
    print(frontend_code)
    
    print("\n" + "="*50 + "\n")
    print("Key Integration Points:")
    print("1. The frontend modal collects all required parameters")
    print("2. The API endpoint matches the frontend data structure exactly")
    print("3. Error handling provides user-friendly messages")
    print("4. Success responses include email tracking IDs")

if __name__ == "__main__":
    print("🎉 Friend Invitation Endpoint Examples\n")
    
    # Run examples
    example_health_check()
    print("\n" + "="*60 + "\n")
    
    example_send_invitation()
    print("\n" + "="*60 + "\n")
    
    example_frontend_integration()
    
    print("\n=== Setup Instructions ===")
    print("1. Set RESEND_API_KEY in your environment variables")
    print("2. Start your FastAPI server: python main.py")
    print("3. Run this example: python example_invitation_usage.py")
    print("4. Check the generated documentation: INVITATION_ENDPOINT_GUIDE.md")
