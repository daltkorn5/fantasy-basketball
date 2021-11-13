# Yahoo Fantasy Sports API Setup

Yahoo has an API that allows you to request data for, 
among other things, fantasy sports. However, their documentation
is terrible, so here is my attempt to outline what I did to
be able to request fantasy basketball data.

## Create a Yahoo Developer application
1. If you don't have one already, you need to create a Yahoo account
2. Then you need to [create an application](https://developer.yahoo.com/apps/create/) on the Yahoo Developer site
    * The only non-intuitive thing here (at least for me) was the "Redirect URI."
      You can set that to be `https://localhost:8080` or whatever port you want.
3. Once you create your application, you'll get a set an Application ID,
   a Client ID, and a Client Secret. The Application ID doesn't matter, but the Client ID
   and Client Secret are needed to authenticate with Yahoo when hitting up the API.
4. Next I would recommend installing the [yahoo-oauth](https://pypi.org/project/yahoo-oauth/)
   library to facilitate authentication. It's very easy to use.
    * To use the `yahoo-oauth` library you pretty much just need a line like
    this in your code to authenticate:
    ```python
    from yahoo_oauth import OAuth2
    oauth = OAuth2(None, None, from_file="oauth_keys.json")
    ```
5. The `from_file` argument to `OAuth2` above is key here. You should create
   a json file that contains your Client ID and Client Secret for the oauth library
   to use for authentication. It should look like:
   ```json
   {
       "consumer_key": "<YOUR CLIENT ID HERE>",
       "consumer_secret": "<YOUR CLIENT SECRET HERE>"
   }
    ```

That should be it! You should be good to go now!
To make a request to Yahoo you can now just do:
```python
response = oauth.session.get("https://fantasysports.yahooapis.com/fantasy/v2/your/endpoint")
```