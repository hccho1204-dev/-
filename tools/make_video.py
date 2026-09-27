import subprocess, os, textwrap
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
FD = "/usr/local/lib/python3.11/dist-packages/koreanize_matplotlib/fonts/"
big = ImageFont.truetype(FD+"NanumGothicExtraBold.ttf", 92)
mid = ImageFont.truetype(FD+"NanumGothicBold.ttf", 50)
small = ImageFont.truetype(FD+"NanumGothicBold.ttf", 40)
W,H = 1080,1920
scenes = [
 (3,"80세,\n출근합니다","일본에선 여든 살 할아버지도\n아침에 출근합니다"),
 (5,"70대\n3명 중 1명\n일한다","일본 70대 초반은\n세 명 중 한 명이 일을 합니다"),
 (4,"TOP 5","이들이 가장 많이 하는 일"),
 (4,"5위\n경비","공사장과 주차장 경비"),
 (4,"4위\n청소·관리인","건물 청소와 관리인"),
 (4,"3위\n편의점","편의점과 마트 계산대"),
 (4,"2위\n택시","택시기사 평균 나이 60세 안팎"),
 (4,"1위\n농업","일본 농부 평균 나이 약 69세"),
 (8,"일 =\n사람 만나는 곳","돈 때문만은 아닙니다.\n일은 월급이 아니라\n'사람을 만나는 곳'"),
 (5,"몇 살까지\n일하고 싶으세요?","한국도 10년 뒤면 똑같아집니다"),
]
os.makedirs("/tmp/frames", exist_ok=True)
lst = open("/tmp/frames/list.txt","w")
for i,(d,cap,sub) in enumerate(scenes):
    img = Image.new("RGB",(W,H))
    dr = ImageDraw.Draw(img)
    for y in range(H):  # dark navy gradient
        t=y/H; dr.line([(0,y),(W,y)], fill=(int(18+20*t),int(24+18*t),int(48+30*t)))
    dr.text((W/2,170),"10년 먼저 늙은 나라",font=small,fill=(255,200,80),anchor="mm")
    dr.multiline_text((W/2,H*0.42),cap,font=big,fill="white",anchor="mm",align="center",spacing=24)
    dr.rectangle([140,H*0.62,W-140,H*0.62+6],fill=(255,200,80))
    dr.multiline_text((W/2,H*0.72),sub,font=mid,fill=(220,225,235),anchor="mm",align="center",spacing=18)
    dr.text((W/2,H-150),f"{i+1}/{len(scenes)}",font=small,fill=(140,150,170),anchor="mm")
    p=f"/tmp/frames/s{i:02d}.png"; img.save(p)
    lst.write(f"file '{p}'\nduration {d}\n")
lst.write(f"file '/tmp/frames/s{len(scenes)-1:02d}.png'\n"); lst.close()
out="/home/user/-/videos/ep01_draft.mp4"
subprocess.run([FF,"-y","-loglevel","error","-f","concat","-safe","0","-i","/tmp/frames/list.txt",
  "-vf","fps=30,format=yuv420p","-c:v","libx264","-movflags","+faststart",out],check=True)
print(out, os.path.getsize(out))
