# napalm_netgear
NAPALM module for netgear switches

Uses netmiko netgear prosafe driver. Tested with M4300 and M4250.

## Implemented APIs
 - open
 - close
 - get_config
 - load_merge_candidate
 - commit_config
 - get_interfaces_ip

*partially implemented:*
 - get_mac_address_table
 - get_interfaces
 - get_interfaces_counters
 - get_facts
 - load_replace_candidate
