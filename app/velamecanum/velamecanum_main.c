/****************************************************************************
 * Contest 2026 team 498 - VelaMecanum formation control entry
 *
 * VelaMecanum is a four-vehicle formation system built on four MentorPi M1
 * mecanum-wheel vehicles.  Missions are issued to the fleet through the
 * openvela ai_agent "formation_control" tool; this NSH application is the
 * on-device entry used to inspect the supported capability set from the
 * serial console.
 *
 * Related sources in this repository:
 *   openvela/ai_agent/src/tools/tool_formation.c   formation_control tool
 *   openvela/ai_agent/src/tools/tool_registry.c    tool registration
 *   outputs/formation-kit/                         fleet mission control
 ****************************************************************************/

#include <nuttx/config.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define VELAMECANUM_VERSION "1.0.0"

static const char *g_formations[] =
{
  "square", "line", "triangle", "circle", "diamond"
};

static const char *g_control_modes[] =
{
  "anchored", "laplacian", "second_order"
};

static void usage(void)
{
  printf("VelaMecanum %s - four-vehicle formation control\n", VELAMECANUM_VERSION);
  printf("Usage: velamecanum <command>\n");
  printf("  help          show this message\n");
  printf("  capabilities  list supported formations and control modes\n");
  printf("  version       show release version\n");
  printf("\n");
  printf("Mission commands (start / status / stop / reset) are issued\n");
  printf("through the ai_agent formation_control tool.\n");
}

static void capabilities(void)
{
  int i;

  printf("{\"ok\":true,\"data\":{");
  printf("\"formations\":[");
  for (i = 0; i < (int)(sizeof(g_formations) / sizeof(g_formations[0])); i++)
    {
      printf("%s\"%s\"", i ? "," : "", g_formations[i]);
    }

  printf("],\"control_modes\":[");
  for (i = 0; i < (int)(sizeof(g_control_modes) / sizeof(g_control_modes[0])); i++)
    {
      printf("%s\"%s\"", i ? "," : "", g_control_modes[i]);
    }

  printf("],\"min_distance_m\":0.30,\"max_linear_mps\":0.875,");
  printf("\"max_acceleration_mps2\":2.0}}\n");
}

int main(int argc, char *argv[])
{
  if (argc < 2)
    {
      usage();
      return EXIT_SUCCESS;
    }

  if (strcmp(argv[1], "help") == 0 || strcmp(argv[1], "-h") == 0)
    {
      usage();
    }
  else if (strcmp(argv[1], "capabilities") == 0)
    {
      capabilities();
    }
  else if (strcmp(argv[1], "version") == 0)
    {
      printf("velamecanum %s\n", VELAMECANUM_VERSION);
    }
  else
    {
      printf("velamecanum: unknown command '%s'\n", argv[1]);
      usage();
      return EXIT_FAILURE;
    }

  return EXIT_SUCCESS;
}