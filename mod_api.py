"""
ChaoHub Modding/Plugin API System Specification
================================================
Define the structural contract that all third-party mods must implement to run inside
the ChaoHub desktop ecosystem.
"""

class BaseMod:
    """
    Foundational API contract base class that mod creators reference and inherit.
    """
    def initialize(self, app_instance):
        """
        Grants the mod a secure handle to the main ChaoHubApp memory tree to register
        custom components (e.g., custom modules or visual theme hooks).

        Args:
            app_instance (ChaoHubApp): The main application context instance.
        """
        pass

    def teardown(self):
        """
        Invoked during system shutdown to cleanly unbind assets, stop background loops,
        or release visual hooks.
        """
        pass

# Example of the CHAO_MOD_MANIFEST dictionary that every mod .py file must export:
# 
# CHAO_MOD_MANIFEST = {
#     "name": "MY_COOL_MOD",
#     "author": "Hacker",
#     "version": "1.0.0",
#     "type": "NEW_MODULE",           # 'NEW_MODULE' or 'VISUAL_EFFECT'
#     "entry_point": "MyModClass"      # Name of the class to instantiate
# }
