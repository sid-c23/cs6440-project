# cs6440-group-project

## Backend setup

Taken from [FastAPI Docs](https://fastapi.tiangolo.com/#installation):

- Create a [virtual environment](https://fastapi.tiangolo.com/virtual-environments/#create-a-virtual-environment)
- Activate the virtual environment with `source .venv/bin/activate`
- Use `pip install -r requirements.txt`
- `cd backend/` and then run `fastapi dev main.py`

The API should be available for view at [`http://localhost:8000/docs/`](http://localhost:8000/docs/)

### Key Notes

* To update the schema of the sqlite database, make the updates, **delete** app.db, and then restart the server.
The schema will update after the server has restarted. Note that this will delete the database data, so it should be used
for testing.

* `main.py` contains the API routes
* The `User` and `Event` classes in `models.py` are the database schemas.
* `schemas.py` have class representations of the API request and response types. For example, `schemas.UserRequest`
represents POST request data for a `models.User` type.


## Frontend setup

We use Vue.js V3 which can be found [here](https://vuejs.org/guide/introduction.html).

So far, we use the composition API preference.

Setup follows [this doc](https://vuejs.org/guide/quick-start.html#creating-a-vue-application).

- Set up the Node Version Manager (NVM): `nvm use lts/jod`.
- `cd frontend/` and run `npm install`.
- Use `npm run dev` to start the node server.

The frontend website should be viewable at `http://localhost:5173/`

## Key Points

* The individual pages should be located in `frontend/views`
* Each file is used as a single file component, and examples can be found at
[https://vuejs.org/examples/#hello-world](https://vuejs.org/examples/#hello-world)
* For API calls, we use [axios](https://github.com/axios/axios).