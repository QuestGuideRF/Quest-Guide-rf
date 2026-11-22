from aiogram .fsm .state import State ,StatesGroup
class AdminCityStates (StatesGroup ):
    name =State ()
    description =State ()
    photo =State ()
class AdminRouteStates (StatesGroup ):
    city =State ()
    name =State ()
    description =State ()
    route_type =State ()
    distance =State ()
    estimated_duration =State ()
    price =State ()
class AdminPointStates (StatesGroup ):
    name =State ()
    description =State ()
    task_text =State ()
    fact_text =State ()
    order =State ()
    require_pose =State ()
    min_people =State ()
    reference_photos =State ()
class AdminUserStates (StatesGroup ):
    search =State ()
    message =State ()
class AdminSettingsStates (StatesGroup ):
    similarity_threshold =State ()
    max_photos_per_hour =State ()