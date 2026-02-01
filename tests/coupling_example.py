"""Example showing class coupling for demonstration."""


class DataStore:
    """
    Handles data persistence.

    ::: This is-in-layer Test-Layer.
    ::: This is a fixture.
    """

    def save(self, data):
        """Save data to store."""
        return f"Saved: {data}"

    def load(self, key):
        """Load data from store."""
        return f"Data for {key}"


class Cache:
    """Caching layer."""

    def __init__(self):
        self.store = DataStore()  # Inheritance-like coupling

    def get(self, key):
        """Get from cache or fall back to store."""
        # Calls DataStore.load - creates coupling
        return self.store.load(key)

    def set(self, key, value):
        """Set cache value."""
        # Calls DataStore.save - creates coupling
        self.store.save(f"{key}={value}")


class UserService:
    """Handles user operations."""

    def __init__(self):
        self.cache = Cache()
        self.store = DataStore()

    def get_user(self, user_id):
        """Get user by ID."""
        # Calls Cache.get - creates coupling
        cached = self.cache.get(user_id)
        if not cached:
            # Calls DataStore.load - creates coupling
            return self.store.load(user_id)
        return cached

    def save_user(self, user_id, data):
        """Save user data."""
        # Calls DataStore.save - creates coupling
        self.store.save(data)
        # Calls Cache.set - creates coupling
        self.cache.set(user_id, data)


class NotificationService:
    """Sends notifications."""

    def __init__(self):
        self.user_service = UserService()

    def notify_user(self, user_id, message):
        """Notify a specific user."""
        # Calls UserService.get_user - creates coupling
        user = self.user_service.get_user(user_id)
        return f"Notifying {user}: {message}"

    def broadcast(self, message):
        """Broadcast to all users."""
        return f"Broadcasting: {message}"
