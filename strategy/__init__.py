from strategy.registration import RegistrationAssistant
from strategy.advanced_strategy import AdvancedRegistrationAssistant

# Define available strategies for dynamic loading
STRATEGIES = {
    'default': {'class': RegistrationAssistant, 'description': 'Basic registration strategy'},
    'advanced': {'class': AdvancedRegistrationAssistant, 'description': 'Advanced registration with optimal timing'}
}