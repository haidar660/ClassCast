

How to Reproduce the Exact Experiments From the Report
git clone <repo_url>
cd classcast

# 1. Create environment
pip install -r requirements.txt

# 2. Create your .env
cp .env.example .env
# fill in API keys

# 3. Ensure test videos exist
ls data/test_videos/

# 4. Run all experiments
python scripts/run_all_experiments.py


All results will appear under:

test_output/runs/