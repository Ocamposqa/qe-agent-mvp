import random
import string
from langchain_core.tools import StructuredTool

class SyntheticDataAgent:
    """
    Skill for generating localized dummy data (Email, CreditCard, Address).
    Exposes an interface for other agents to request data seamlessly.
    """
    def generate_email(self):
        domain = random.choice(["example.com", "test.org", "quantumqe.io"])
        prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}@{domain}"

    def generate_credit_card(self):
        # 16 digit dummy visa
        return "4" + ''.join(random.choices(string.digits, k=15))

    def generate_address(self):
        streets = ["Main St", "Oak Ave", "Pine Ln", "Maple Dr"]
        cities = ["Springfield", "Rivertown", "Lakeview", "Hill Valley"]
        return f"{random.randint(100, 9999)} {random.choice(streets)}, {random.choice(cities)}"

    def get_tools(self):
        return [
            StructuredTool.from_function(
                name="GenerateSyntheticEmail",
                func=self.generate_email,
                description="Generates a random valid synthetic email address."
            ),
            StructuredTool.from_function(
                name="GenerateSyntheticCreditCard",
                func=self.generate_credit_card,
                description="Generates a random valid synthetic 16-digit credit card number."
            ),
            StructuredTool.from_function(
                name="GenerateSyntheticAddress",
                func=self.generate_address,
                description="Generates a random valid synthetic physical address."
            )
        ]
