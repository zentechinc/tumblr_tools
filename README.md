# tumblr_cleaner
A tool for managing your Tumblr content in bulk

See the following link for API documentation used to interact with Tumblr: https://github.com/tumblr/pytumblr

About Tumblr OAuth
Tumblr supports OAuth 1.0a, accepting parameters via the Authorization header, with the HMAC-SHA1 signature method only. There's probably already an OAuth client library for your platform. 

If you've worked with Twitter's OAuth implementation, you'll feel right at home with ours.
Request-token URL:
POST https://www.tumblr.com/oauth/request_token
Authorize URL:
https://www.tumblr.com/oauth/authorize
Access-token URL:
POST https://www.tumblr.com/oauth/access_token
Rate Limits
Newly registered consumers are rate limited to 1,000 requests per hour, and 5,000 requests per day. If your application requires more requests for either of these periods, please use the 'Request rate limit removal' link on an app above.

Tumblr supports OAuth 1.0a, accepting parameters via the Authorization header, with the HMAC-SHA1 signature method only. There's probably already an OAuth client library for your platform. 

If you've worked with Twitter's OAuth implementation, you'll feel right at home with ours.
Request-token URL:
POST https://www.tumblr.com/oauth/request_token
Authorize URL:
https://www.tumblr.com/oauth/authorize
Access-token URL:
POST https://www.tumblr.com/oauth/access_token
Rate Limits

// Authenticate via OAuth
var tumblr = require('tumblr.js');
var client = tumblr.createClient({
  consumer_key: 'key_here',
  consumer_secret: 'secret here',
  token: 'token_here',
  token_secret: 'token_secret_here'
});
