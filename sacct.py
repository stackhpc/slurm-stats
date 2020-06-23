from datetime import datetime
import subprocess
from ClusterShell import NodeSet

args = ["sacct", "-X", "--allusers", "--parsable2", "--format",
        "jobid,jobidraw,cluster,partition,account,group,gid,"
        "user,uid,submit,eligible,start,end,elapsed,exitcode,state,nnodes,"
        "ncpus,reqcpus,reqmem,reqgres,reqtres,timelimit,nodelist,jobname",
        "--state",
        "CANCELLED,COMPLETED,FAILED,NODE_FAIL,PREEMPTED,TIMEOUT"]

SLURM_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
TIMESTAMP_FILE = "lasttimestamp"

# Work out statetime and endtime
now = datetime.utcnow()
end_str = now.strftime(SLURM_DATE_FORMAT)

try:
    with open(TIMESTAMP_FILE) as f:
        start_str = f.read()
except FileNotFoundError:
    # Default to start of today
    start_str = "00:00:00"

args += ["--starttime", start_str]
args += ["--endtime", end_str]

#print(" ".join(args))
process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")

# Use the title line to work out the attribute order
lines = process.stdout.split("\n")
titles_line = lines[0]
attributes = titles_line.split("|")

# Try to output any errors we might have hit
if len(attributes) < 3:
    print(lines)
    exit(-1)

# Parse each line of sacct output into a dict
items = []
for line in lines[1:]:
  components = line.split("|")
  if len(components) != len(attributes):
      continue
  item = {}
  for i in range(len(attributes)):
      item[attributes[i]] = components[i]

  # Unpack NodeList format, so its easier to search for hostnames
  nodelist = item.get("NodeList")
  if nodelist:
      nodeset = NodeSet.NodeSet(nodelist)
      nodes = list([x for x in nodeset])
      item["AllNodes"] = nodes

  # Exclude job steps
  jobid = item.get("JobID")
  if jobid and "." not in jobid:
      items.append(item)
      print(item)

# Write out timestamp, so we know where to start next time
with open(TIMESTAMP_FILE, 'w') as f:
   f.write(end_str)

#print(len(items))
