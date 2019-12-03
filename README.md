# BibDeskQuery

An Alfred workflow to search BibDesk, open files, or create citation commands. 

The workflow is made for Alfred 3, but is compatible with Alfred 4. The basic options are:

    "bb X" = search all bibligraphic fields within BibDesk for X
    "bt X" = search titles within BibDesk for X
    "ba X" = search authors/editors within BibDesk for X

This is what the first option looks like, after I typed in "Cohen":

![BibDesk Lookup](https://zbiener.github.io/images/2016-06-06-searching-bibdesk-1.png)

Now several actions are possible, depending on which modifier keys you press:

    + enter = open the entry in BibDesk
    + shift+enter = open the file associated with the entry (the plus sign in the entry's icon indicates that there is a file associated with it).
    + cmd+enter = copy the citation into the clipboard.
    + opt+enter = search the BibDesk GUI using the original search term.
    + ctrl+enter = change the search scope, either narrow to author or titles, or broader from authors or title to all search fields (this is like starting the search over).


The citation option is the most complicated and the most useful. After selecting it, you are prompted to enter a page range for the citation (you can leave it blank) and a citation format. I use Pandoc and LaTeX, but it is easy to add/remove other formats from within Alfred.

![](https://zbiener.github.io/images/2016-06-06-searching-bibdesk-2.jpg)

Then, depending on your selection, you'll get a notification of the item copied into the clipboard. If you are in an active text field --- i.e., if you do all this when working in Word, for example --- the entry is pasted automatically. It looks like this:

![](https://zbiener.github.io/images/2016-06-06-searching-bibdesk-3.png)

The Workflow is based on BibQuery by Hackademic. I modified it to use JSON (instead of XML), and modified the way it interacts with Alfred. Consequently, there is also a lot of dead code in the python scripts. I left it there with the hopes of one day making more search options (keyword, group, etc.) available. The entire flow looks like this:

![](https://zbiener.github.io/images/2016-06-06-searching-bibdesk-4.jpg)
