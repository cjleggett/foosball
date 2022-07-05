git checkout slack-bot-graphs
git add $1
git commit -m "Upload elo graph for date $2"
git push my-fork
git checkout slack-bot