Extracts all files from a HAR archive. Automatically combines partial content responses and handles duplicate file names. Useful for when you want to save all the responses from the network tab on your browser without resending requests.
Make sure to set `devtools.netmonitor.responseBodyLimit` to 0 so that Firefox won't truncate long responses.
