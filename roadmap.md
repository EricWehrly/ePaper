next:
- drag and drop to upload and convert

then:
- conversion comparison test between source image types (currently: jpg and png. leave a todo for google's dumb heic)

then:
- install / uninstall scripts for running display controller as a pi system service

later:
- google photos integration on the webserver, if we can

later:
- make albums or books or whatever that will cycle a selected set of images

nice to have:
- color pallete selector in top-right with localstorage persistence

tech debt:
- the autoplay timer needs to be how long images are displayed, and not take into account how long it takes them to be drawn
- our prev and next buttons work but provide no feedback
- requestAnimationFrame in the frontend to reduce pressure
- look into websockets anad worker threads -- want to keep server pressure low
- our "display busy" indicator is currently in the lower left but I would prefer the middle top
- add an "active" indicator in "Available images"