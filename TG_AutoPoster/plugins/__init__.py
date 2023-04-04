from .callback import (delete_domain, reposts_config, show_option,
                       switch_option, wts_config, set_param)
from .commands import (about, add_source, cancel, exit_, get_config,
                       get_id, register, remove_source, restart,
                       send_full_logs, send_last_logs, send_welcome, settings,
                       update_blacklist, update_stoplist, delete_stoplist)
from .handlers import update_header_footer, get_forward_id, stoplist_update
from .inline import inline
