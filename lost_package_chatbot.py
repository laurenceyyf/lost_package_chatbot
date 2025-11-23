"""
Lost Package Chatbot
Flowchart:
- Start -> greet -> ask tracking ID
    - Invalid format? -> explain format -> re-prompt (2 tries) -> fallback to email + zipcode lookup
    - Valid -> derive package status (sample data) -> branch:
        - In transit -> share ETA -> offer SMS updates -> confirm anything else -> end
        - Delayed -> share reason -> offer pickup location change -> confirm anything else -> end
        - Suspected lost -> start claim -> collect delivery description -> provide reference -> offer human transfer -> end
- At any yes/no prompt:
    - Invalid input -> clarify accepted responses -> re-prompt with examples
"""
import random
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


def prompt_until_valid(
    question: str,
    validator: Callable[[str], bool],
    error_message: str,
    max_attempts: int = 2,
) -> Tuple[Optional[str], bool]:
    """
    Ask the user for input until it passes validation or attempts run out.
    Returns (value, success_flag).
    """
    for attempt in range(max_attempts):
        answer = input(question).strip()
        if validator(answer):
            return answer, True
        print(error_message)
    return None, False


def ask_yes_no(question: str) -> bool:
    """Ask a yes/no question with resilient handling of unexpected inputs."""
    normalized_yes = {"y", "yes", "yeah", "sure"}
    normalized_no = {"n", "no", "nope"}
    while True:
        reply = input(question + " (yes/no): ").strip().lower()
        if reply in normalized_yes:
            return True
        if reply in normalized_no:
            return False
        print("I caught that as something else. Please reply with yes or no (e.g., 'yes').")


def looks_like_tracking(tracking_id: str) -> bool:
    stripped = tracking_id.replace("-", "")
    return stripped.isalnum() and 8 <= len(stripped) <= 14


@dataclass
class PackageStatus:
    status: str
    details: str
    eta: Optional[str] = None


class LostPackageChatbot:
    def __init__(self) -> None:
        pass

    def greet(self) -> None:
        print("Hi, I help locate packages quickly.")

    def derive_status(self, tracking_id: str) -> PackageStatus:
        """
        Return a deterministic status so the flow is predictable for demos.
        Falls back to a pseudo-random but repeatable assignment.
        """
        normalized = tracking_id.upper()

        bucket = sum(ord(c) for c in normalized) % 3
        if bucket == 0:
            return PackageStatus("in_transit", "Arrived at regional facility", eta="Tomorrow by 7pm")
        if bucket == 1:
            return PackageStatus("delayed", "Missed connection; awaiting next dispatch", eta="+1 day")
        return PackageStatus("lost", "No scans in the last 48 hours.")

    def handle_in_transit(self, status: PackageStatus) -> None:
        print(f"Good news: your package is in transit. {status.details}")
        if status.eta:
            print(f"Estimated delivery: {status.eta}")
        wants_updates = ask_yes_no("Would you like SMS updates for each movement?")
        if wants_updates:
            print("SMS alerts enabled. You'll get notifications for departures and arrival.")
        else:
            print("No problem. You can ask for updates anytime.")
        self.closing()

    def handle_delayed(self, status: PackageStatus) -> None:
        print(f"I see a delay: {status.details}")
        if status.eta:
            print(f"New estimated delivery: {status.eta}")
        reroute = ask_yes_no("Do you want to reroute to a nearby pickup locker?")
        if reroute:
            print("Locker reserved at your nearest location. We'll ship there on the next truck.")
        else:
            print("We'll keep it on the home delivery path and monitor closely.")
        self.closing()

    def handle_lost(self, status: PackageStatus) -> None:
        print(f"I can't see recent scans. {status.details}")
        start_claim = ask_yes_no("Should I start a lost-package investigation?")
        if start_claim:
            description = input("Describe the packaging or any distinguishing marks: ").strip()
            print(
                "Claim opened. Ref: LP-"
                f"{random.randint(1000, 9999)}. "
                "We'll contact you within 24 hours."
            )
            if description:
                print("Noted description:", description)
        else:
            print("Understood. I'll watch for new scans and alert you if anything changes.")
        self.closing()

    def closing(self) -> None:
        anything_else = ask_yes_no("Need help with anything else on this package?")
        if anything_else:
            print("I'm here for tracking, reroutes, and claims. Restart me to pick another option.")
        else:
            print("Thanks for using Trace. Have a great day!")

    def fallback_lookup(self) -> None:
        email = input("Enter the email used for the order: ").strip()
        postal = input("Enter the delivery ZIP/postal code: ").strip()
        if email and postal:
            print("Thanks. I've found the order and filed a ticket to trace the package.")
        else:
            print("I need both pieces of info to proceed. Handing off to an agent for help.")
        print("An agent will follow up shortly. Conversation ended.")

    def run(self) -> None:
        self.greet()
        tracking_id, ok = prompt_until_valid(
            "What's the tracking ID? (letters/numbers, 8-14 chars): ",
            looks_like_tracking,
            "That format looks off. Try something like ZX-12345678 (8-14 letters/numbers).",
        )
        if not ok:
            print("Let's try another way.")
            self.fallback_lookup()
            return

        status = self.derive_status(tracking_id)
        if status.status == "in_transit":
            self.handle_in_transit(status)
        elif status.status == "delayed":
            self.handle_delayed(status)
        else:
            self.handle_lost(status)


if __name__ == "__main__":
    try:
        LostPackageChatbot().run()
    except KeyboardInterrupt:
        sys.exit("\nSession cancelled. Restart anytime.")
