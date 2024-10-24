import sys
from tkinter import font
from tkinter.messagebox import askyesno, showwarning
import yt_dlp
from tkinter import *
from tkinter.ttk import *
import subprocess
import os
import winsound
import pathlib
import re

os.system( 'cls' )

padding          = { 'padx'   : 5,  'pady'  : 5 }
labels_gridO     = { 'sticky' : 'E' }

styles_spinners  = { 'width'  : 10 }
options_spinners = { 'from_'  : 0, 'to_'    : 59, 'wrap' : True }
options_buttons_small = { 'width' : 2 }


main        = Tk()
main.title( 'yt-dlp' )

font_large       = font.Font( family = "Courier", size = 12 )

s           = Style()
s.configure( '.', font = ( '', 15 ) )

def callBack( var = '', index = '', mode = '', destFilename = "" ):

    global finalCommand
    
    text_command.replace( '1.0', END, f'{ytdlPath} \n"{url.get()}" \n --console-title' )
    finalCommand = [ ytdlPath, url.get(), '--console-title' ]
    
    if( not os.path.exists( destination.get() ) ):
        text_command.insert( END, f' \n-P "D:\Stuff\down\youtube-dl\downloaded"' )
        finalCommand.extend( [ '-P', 'D:\Stuff\down\youtube-dl\downloaded' ] )
    else:
        text_command.insert( END, f' \n-P "{destination.get()}"' )
        finalCommand.extend( [ '-P', destination.get() ] )


    if( cb_smallest.get() ):
        text_command.insert( END, ' \n-S "+size,+br"' )
        finalCommand.extend( [ '-S', '+size,+br' ] )
    
    if( f_h.get() or f_m.get() or f_s.get() or t_h.get() or t_m.get() or t_s.get() ):
        text_command.insert( END, f' \n-f "(bestvideo+bestaudio/best)[protocol!*=dash]" \n--external-downloader ffmpeg \n--external-downloader-args "ffmpeg_i:-ss {f_h.get()}:{f_m.get()}:{f_s.get()}')
        extDownArgs = f'ffmpeg_i:-ss {f_h.get()}:{f_m.get()}:{f_s.get()}'
        if( t_h.get() or t_m.get() or t_s.get() ):
            text_command.insert( END, f' -to {t_h.get()}:{t_m.get()}:{t_s.get()}' )
            extDownArgs = extDownArgs + f' -to {t_h.get()}:{t_m.get()}:{t_s.get()}'
        text_command.insert( END, '"' )
        finalCommand.extend( [ '-f', '(bestvideo+bestaudio/best)[protocol!*=dash]', '--external-downloader', 'ffmpeg', '--external-downloader-args', extDownArgs ] )

    if( destFilename ):
        text_command.insert( END, f' \n-o "{destFilename}"' )
        finalCommand.extend( [ '-o', destFilename ] )

    if( cb_browser.get() ):
        text_command.insert( END, ' \n--cookies-from-browser Vivaldi' )
        finalCommand.extend( [ '--cookies-from-browser', 'Vivaldi' ] )

    #print( finalCommand )

def getClipboard():
    url.set( main.clipboard_get() )

def openPath():
    os.startfile( destination.get() )

def generateFN():

    tx        = txt_outtmpl.get( '1.0', END )
    
    if( len( tx ) > 1 ):
        ytdl_opts = { 'outtmpl' : tx }
        fn        = getFileName( ytdl_opts )
    else:
        fn        = getFileName()
    
    fn        = re.sub( '#$', '', fn)
    txt_prev.replace( '1.0', END, fn )
    return fn

def setTemplate(  var = '', index = '', mode = '' ):
    if( url.get().find( 'youtube.com/' ) !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(uploader_id)s [yt] - %(uploader)s - %(title)s - %(id)s.%(ext)s' )
    if( url.get().find( 'tiktok.com/') !=-1 ):
        print( url.get().find( 'tiktok.com/') !=-1 )
        txt_outtmpl.replace( '1.0', END, "%(uploader)s [tik] - %(creator)s - %(title)s - %(track)s - %(id)s.%(ext)s" )
    if( url.get().find( 'twitter.com/') !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(uploader_id)s[tw] - %(uploader)s - %(title)s - %(id)s.%(ext)s' )
    if( url.get().find( 'facebook.com/') !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(uploader_id)s [fb] - %(uploader)s - %(title)s - %(id)s.%(ext)s' )
    if( url.get().find( 'instagram.com/') !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(uploader_id)s [ig] - %(uploader)s - %(title)s - %(description)s - %(id)s.%(ext)s' )
    if( url.get().find( 'xvideos.com/') !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(title)s [xv] - %(id)s.%(ext)s' )
    if( url.get().find( 'zee5.com/') !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(display_id) [zee] - S%(season_number)E%(episode_number) - %(upload_date) - %(title)s - %(id)s.%(ext)s' )
    if( url.get().find( 'voot.com/' ) !=-1 ):
        txt_outtmpl.replace( '1.0', END, '%(title)s [voot] - %(episode)s - %(id)s.%(ext)s' )

def checkDest( var = '', index = '', mode = '' ):
    if( not os.path.exists( destination.get() ) ):
        ent_dest.config( { 'foreground' : 'red' } )
        return False
    else:
        ent_dest.config( { 'foreground' : '' } )
        return True

url         = StringVar( main, value = sys.argv[1] if len( sys.argv ) > 1 else '' )
url.trace_add( 'write', callBack )
url.trace_add( 'write', setTemplate )

ytdlPath = 'D:\Stuff\down\youtube-dl\yt-dlp.exe' ''

destination = StringVar( main, value='' )
destination.trace_add( 'write', callBack )
destination.trace_add( 'write', checkDest )
destination.set( "W:\\#ytd\\" )

frame_main  = Frame( main )

Label(  frame_main, text = 'URL :',                            ).pack( side = 'left', fill='both' )
ent_url = Entry(  frame_main, textvariable = url,           ).pack( side = 'left', fill='both', expand=True, )
Button( frame_main, text = '📋', command = getClipboard, **options_buttons_small ).pack( side = 'left')

frame_main2 = Frame( main )

Label( frame_main2, text = 'Destination :'                    ).pack( side='left' )
ent_dest = Entry( frame_main2, textvariable = destination )
ent_dest.pack( fill='both', expand=True, side = 'left' )
Button( frame_main2, text = '📁', command = openPath, **options_buttons_small ).pack( side = 'left' )

frame_main3 = Frame( main )

Label( frame_main3, text = 'Outtmpl :' ).pack( side = 'left' )
txt_outtmpl = Text( frame_main3, font=font_large, height = 2 )
txt_outtmpl.pack( fill='both', expand=True, side = 'left' )
frame_main4 = Frame( main )

Label( frame_main4, text = 'Prev :' ).pack( side = 'left' )
txt_prev = Text( frame_main4, height = 3, width = 10  )
txt_prev.pack( fill='both', expand=True, side = 'left' )
txt_prev.configure(font=font_large)
Button( frame_main4, text = '🧬', command = generateFN, **options_buttons_small ).pack( side = 'left' )


frame_checkbtns = Frame( main )

cb_browser = IntVar()
cb_browser.trace_add( 'write', callBack )
Checkbutton( frame_checkbtns, text = 'Load cookies\nfrom browser', variable = cb_browser ).pack( side='left' )

cb_smallest = IntVar()
cb_smallest.trace_add( 'write', callBack )
Checkbutton(      frame_checkbtns, text = 'Smallest',                   variable = cb_smallest).pack()

f_h, f_m, f_s, t_h, t_m, t_s = IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()
f_h.trace_add( 'write', callBack )
f_m.trace_add( 'write', callBack )
f_s.trace_add( 'write', callBack )
t_h.trace_add( 'write', callBack )
t_m.trace_add( 'write', callBack )
t_s.trace_add( 'write', callBack )

frame_2 = Frame( main )
Label(   frame_2, text = 'Start :',                        ).grid( row = 0, column = 0, **labels_gridO )
Spinbox( frame_2, from_ = 0, to_ = 1000, **styles_spinners, textvariable = f_h ).grid( row = 0, column = 1 )
Spinbox( frame_2, **options_spinners,    **styles_spinners, textvariable = f_m ).grid( row = 0, column = 2 )
Spinbox( frame_2, **options_spinners,    **styles_spinners, textvariable = f_s ).grid( row = 0, column = 3 )
Label(   frame_2, text = 'End :'  ,                        ).grid( row = 0, column = 4, **labels_gridO )
Spinbox( frame_2, from_ = 0, to_ = 1000, **styles_spinners, textvariable = t_h ).grid( row = 0, column = 5 )
Spinbox( frame_2, **options_spinners,    **styles_spinners, textvariable = t_m ).grid( row = 0, column = 6 )
Spinbox( frame_2, **options_spinners,    **styles_spinners, textvariable = t_s ).grid( row = 0, column = 7 )

frame_main.grid(  sticky='nsew' )
frame_main2.grid( sticky='nsew' )
frame_main3.grid( sticky='nsew' )
frame_main4.grid( sticky='nsew' )
Separator( main, orient = HORIZONTAL ).grid( sticky = "ew", pady=20 )
frame_checkbtns.grid()
Separator( main, orient = HORIZONTAL ).grid( sticky = "ew", pady=20 )
frame_2.grid()


def getFileName( ytdopts = '' ):
    url_      = url.get()
    info_dict = yt_dlp.YoutubeDL( ytdopts if ytdopts else None ).extract_info(     url_, download=False)
    out       = yt_dlp.YoutubeDL( ytdopts if ytdopts else None ).prepare_filename( info_dict )
    return out

def check_file(filePath):
    if os.path.exists(filePath):
        numb = 1
        while True:
            newPath = "{0} _{2}{1}".format(*os.path.splitext(filePath) + (numb,))
            if os.path.exists(newPath):
                numb += 1
            else:
                return newPath
    return filePath

def run():

    if not checkDest():
        destination.set( 'D:\Stuff\down\youtube-dl\downloaded' )
        checkDest()

    os.system( 'cls' )
    print( finalCommand )

    ytdopts = { 'outtmpl' : txt_outtmpl.get( '1.0', 'end' ) }

    fn = generateFN()

    newFN = pathlib.PurePath(check_file( f'{destination.get()}\{fn}' ) ).name
    
    if( len( newFN ) > 200 ):
        showwarning( '', len( newFN ) )

    response = askyesno( 'Confirm', f'Download "{newFN}" ?' )

    if( response ):

        callBack( None, None, None, newFN)

        subprocess.run( finalCommand )
        winsound.Beep( 1000, 250 )

        def dismiss():
            finished.grab_release()
            finished.destroy()

        def buttonClick( whichButton ):
            print( whichButton )
            print( cb_exit.get() )
            match whichButton:
                case 'exit':
                    os._exit( 1 )

        finished = Toplevel( main )
        finished.title( 'Download condluded' )
        finished.attributes("-topmost", 1)
        finished.protocol("WM_DELETE_WINDOW", dismiss) # intercept close button
        finished.transient( main )   # dialog window is related to main
        finished.wait_visibility() # can't grab until window appears, so we wait
        finished.grab_set()        # ensure all input goes to our window
        cb_exit = IntVar()
        Checkbutton( finished, text = 'Exit', variable = cb_exit ).pack()
        Button( finished, text = 'Path', command = lambda: buttonClick( 'path' ) ).pack( side = 'left' )
        Button( finished, text = 'File', command = lambda: buttonClick( 'file' ) ).pack( side = 'left' )
        Button( finished, text = 'Exit', command = lambda: buttonClick( 'exit' ) ).pack( side = 'left' )
        finished.wait_window()     # block until window is destroyed

        
        finished.mainloop()

def run2():

    ytdl_opts = { 'outtmpl' : '%(id)s' }
    showwarning( None, getFileName() )


    # url_ = url.get()


    # with yt_dlp.YoutubeDL( ytdl_opts ) as ydl:
    #     info_dict = ydl.extract_info( url_, download=False)
    #     out = ydl.prepare_filename( info_dict )
    #     print( out ) 


    # asss = yt_dlp.YoutubeDL()
    # return


Button( main, text = 'Run', command = run  ).grid( **padding, sticky = 'ew' )
Button( main, text = 'Run', command = run2 ).grid( **padding)
text_command = Text( main, height = 9 )

callBack()
setTemplate()

text_command.grid()

main.mainloop()