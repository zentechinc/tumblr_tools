#tumblr_cleaner
A suite of tools for managing your Tumblr content in bulk

See the following links for SDK and API documentation used to interact with Tumblr:<br>
* https://github.com/tumblr/pytumblr<br>
* https://www.tumblr.com/docs/en/api/v2

#intro

This set of tools was built for fun and to clean up my long deprecated blog

Working with the Tumblr Rest API is difficult because Tumblr itself is actually quite buggy, API calls are rate limited, and rate limit violations/thresholds are handled ambiguously and incosistently on Tumblr's part.

For example: cycling through likes quickly will hit rate limits, and Tumblr will respond accordingly and tumblr_tools will sleep until it finds the throttling has been lifted, but if you simply start up the tumblr_tools while your thresholds are cooling, Tumblr will just return empty results without indicating throttling is in affect and tumblr_tools has no way to detect the throttle and will then proceed to exit.

Also: Tumblr's Like and Follow counts are NOT to be trusted in any way; this is a known issue with Tumblr.

I don't intend to work on this thing much any more, but if you have any questions or would like to contribute, please feel free to comment or commit. I can't guarantee I'll see it very quickly, but I'd love to help where time allows.

Use these tools at your own risk.

#musings/hints

##inflated/inaccurate Follow and Like counts

I suspect that there may actually be corruption in the post entries that prevents things from pulling and displaying correctly.

While I can't confirm this without digging through Tumblr's code and databases, I've found that if you reach what Tumblr says is then end of your chain of likes/follows try unliking/unfollowing a thing and then reliking/refollowing it.

For me, this seemed will fix issues with being able to fetch content deeper in my lists. 

This phenomenon also leads me to believe Tumblr has either some corruption in their posts that can be fixed by re-persisting things in their backend AND/OR they have some incompatibility within their content that they have failed to properly migrate or code for. 

If anyone has any insight here, please feel free to share. 

#technicals

I don't intent to make this a full app that you can launch on your phone or anything like that. It was mainly built for personal use; hence the rough way of authenticating as described below.

You must authenticate with Tumblr in order for tumblr_tools to find and interact with your account.

Authentication can be done in two ways: AWS Secrets Manager OR by hard-coding creds in config.py.

Register an api key with Tumblr (https://www.tumblr.com/oauth/apps), it's not hard. Add those credentials to lines 33-26 in config.py, make sure load_from on line 31 is set to 'config', and then you're good to go.

If you wanna use AWS's Secrets Manager (which I recommend because it's cool, powerful and easy to learn), then you can set 31 to 'aws', register a secret in AWS Secrets Manager named 'tumblr_creds' with all 4 secret values ('consumer_key', 'consumer_secret', 'oauth_token', 'oauth_secret') and away you go!

Finally, lines 10-24 represent options for what you want tumblr_tools to do on a given run. The program is laid out in a way to minimize calls, but because my paranoia with regard to Tumblr itself actually properly responding, I prioritize archive and capture requests BEFORE deletes, unfollows or unlikes.

Archive requests go into a sub-folder from the working directory pathed at './resources/archives' while captures go to './resources/captures'.

An archive request will be saved as a 'file-full-of-json', meaning a line delimited text file where each line is a new json document.

the 'file-full-of-json' thing is a blessing to deal with instead of CSV files since the items returned from Tumblr feature very flexible schema, sparse data values, and unpredictable HTML. It is just much nicer to dump JSON to a file and not have to worry about escaping, sanitizing, headers, etc. Finally, reading the JSON is nicer in that i can just load line by line, test for the presence of an attribute and respond accordingly. CSV is not so forgiving. 

Captures are done by looping through post/like content and saving recognized binaries. Parsing HTML can be interesting, and while i feel i've done an okay job at handling many of the post types, it's possible/certain there are places for assets to be missed in the more free-form post types. However, i havent noticed any asset leaks that i have not already fixed.  
