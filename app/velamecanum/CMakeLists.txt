# Contest 2026 team 498 VelaMecanum - formation control demo
if(CONFIG_LVX_USE_DEMO_CONTEST2026_498_VELAMECANUM)
  nuttx_add_application(
    NAME velamecanum
    SRCS velamecanum_main.c
    STACKSIZE 4096)
endif()