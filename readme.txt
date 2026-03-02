Get your local Git repository on Bitbucket
Step 1: Switch to your repository's directory

cd /path/to/your/repo
Step 2: Connect your existing repository to Bitbucket

git remote add origin https://ndiayeom@bitbucket.org/ndiayeom/blent_python_project.git
git push -u origin main
zuXXCFwfjeRULGsWkd4u

===============================================================================
…or create a new repository on the command line
echo "# blent_python_project" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ndiayeom/blent_python_project.git
git push -u origin main

================================================================================================

…or push an existing repository from the command line
git remote add origin https://github.com/ndiayeom/blent_python_project.git
git branch -M main
git push -u origin main
================================================================================================
alias flask="/home/blent/.local/bin/flask"
================================================================================================
curl -i http://127.0.0.1:5000
curl -i http://127.0.0.1:5000/cart
curl -X POST http://127.0.0.1:5000/cart -H "Content-Type: application/json" -d '{"id": "je8zng", "quantity": 1}'
curl -X POST http://127.0.0.1:5000/cart -H "Content-Type: application/json" -d '{"id": "je8zng"}'
curl -X PATCH http://127.0.0.1:5000/cart -H "Content-Type: application/json" -d '{"id": "aaaaa", "quantity": 1}'
curl -X PATCH http://127.0.0.1:5000/cart -H "Content-Type: application/json" -d '{"id": "je8zng", "quantity": 10}'
curl -X DELETE http://127.0.0.1:5000/cart -H "Content-Type: application/json" -d '{"id": "je8zng"}'
================================================================================================
curl -X POST http://127.0.0.1:5000/api/auth/register -H "Content-Type: application/json" 
    -d '{
        "email": "user1@gmail.com", 
        "mot_de_passe": "user1",
        "nom": "USER1 PETIT",
        "role": "client",
        }'
================================================================================================
curl -i http://127.0.0.1:5000
================================================================================================
flask run --debug