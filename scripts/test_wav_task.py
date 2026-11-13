"""Exercise real WAV playback while the main/display loop does no audio pumping."""
from pathlib import Path
import subprocess
import tempfile
import wave
ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
#pragma once
#include <algorithm>
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
constexpr int pdTRUE=1,pdPASS=1;
constexpr unsigned portMAX_DELAY=~0u;
inline bool failTask=false,failMutex=false;
using SemaphoreHandle_t=std::mutex*;
inline auto xSemaphoreCreateMutex(){return failMutex ? nullptr : new std::mutex;}
inline void vSemaphoreDelete(SemaphoreHandle_t m){delete m;}
inline void xSemaphoreTake(SemaphoreHandle_t m,unsigned){m->lock();}
inline void xSemaphoreGive(SemaphoreHandle_t m){m->unlock();}
struct Task {std::mutex mutex;std::condition_variable cv;int pending=0;};
using TaskHandle_t=Task*;
inline thread_local Task* current=nullptr;
inline int xTaskCreate(void(*fn)(void*),const char*,int stack,void* arg,int priority,TaskHandle_t* out){
 assert(stack==6144 && priority==2);
 if(failTask)return 0;
 auto* task=new Task;*out=task;
 std::thread([=]{current=task;fn(arg);}).detach();return pdPASS;
}
inline void xTaskNotifyGive(Task* t){std::lock_guard lock(t->mutex);t->pending++;t->cv.notify_one();}
inline void ulTaskNotifyTake(int,unsigned){std::unique_lock lock(current->mutex);current->cv.wait(lock,[]{return current->pending>0;});current->pending=0;}
inline void vTaskDelay(int n){std::this_thread::sleep_for(std::chrono::milliseconds(n));}
inline std::vector<uint8_t> wavBytes;
struct File {
 size_t cursor=0;bool opened=false;
 explicit operator bool() const{return opened;}
 bool isDirectory(){return false;}
 File openNextFile(){return {};}
 const char* name(){return "mock.wav";}
 size_t read(uint8_t* dest,size_t len){len=std::min(len,wavBytes.size()-cursor);std::memcpy(dest,wavBytes.data()+cursor,len);cursor+=len;return len;}
 bool seek(size_t pos){if(pos>wavBytes.size())return false;cursor=pos;return true;}
 size_t position(){return cursor;}
 size_t available(){return opened ? wavBytes.size()-cursor : 0;}
 void close(){opened=false;}
};
struct FS {bool missing=false;File open(const char*,const char* =nullptr){File f;f.opened=!missing;return f;}};
inline FS LittleFS;
inline uint8_t settingsVolume(){return 100;}
inline bool initAudioStorage(){return true;}
inline void serialLogPrint(const char*){}
inline void serialLogPrintln(const char*){}
inline std::atomic<size_t> fed{0};
inline void writeMonoToSpeaker(const int16_t*,size_t count,uint8_t volume){
 assert(volume==100);
 std::this_thread::sleep_for(std::chrono::microseconds(count*1000000/22050));fed+=count;
}
'''
CHECK = r'''
#include "src/audio/wav_stream.cpp"
int main(int argc,char** argv){
 assert(argc==2);std::ifstream f(argv[1],std::ios::binary);
 wavBytes.assign(std::istreambuf_iterator<char>(f),{});
 failMutex=true;assert(!wavStreamStart(WavClip::Welcome));failMutex=false;
 failTask=true;assert(!wavStreamStart(WavClip::Welcome));failTask=false;
 LittleFS.missing=true;assert(!wavStreamStart(WavClip::Welcome));LittleFS.missing=false;
 assert(wavStreamStart(WavClip::Welcome));
 // No wavStreamUpdate calls: simulate the OLED/main loop blocking for 160 ms.
 std::this_thread::sleep_for(160ms);assert(fed>=2048);
 auto deadline=std::chrono::steady_clock::now()+800ms;
 while(wavStreamIsActive() && std::chrono::steady_clock::now()<deadline)std::this_thread::sleep_for(5ms);
 assert(!wavStreamIsActive() && fed==8192);assert(!wavStreamUpdate());
 fed=0;assert(wavStreamStart(WavClip::Attention));
 assert(wavStreamIsPlaying(WavClip::Attention) && !wavStreamIsPlaying(WavClip::Welcome));
 while(fed==0)std::this_thread::sleep_for(1ms);
 wavStreamStop();const auto stopped=fed.load();
 std::this_thread::sleep_for(70ms);assert(fed==stopped && !wavStreamIsActive());
 fed=0;assert(wavStreamStart(WavClip::Error));wavStreamStop();
 const auto final=fed.load();std::this_thread::sleep_for(50ms);assert(fed==final);
 std::_Exit(0); // The embedded audio task is intentionally permanent.
}
'''
def main():
    with tempfile.TemporaryDirectory(prefix='tiny-wav-task-') as tmp:
        d=Path(tmp)
        for name in ['Arduino.h','ESP_I2S.h','FS.h','LittleFS.h','freertos/FreeRTOS.h','freertos/task.h','freertos/semphr.h','settings/settings.h','serial_log.h','audio/audio.h']:
            p=d/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_text('#include "mock.h"\n')
        (d/'mock.h').write_text(MOCK);(d/'check.cpp').write_text(CHECK)
        wav=d/'sample.wav'
        with wave.open(str(wav),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050);w.writeframes(b'\x10\x00'*8192)
        subprocess.run(['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror',f'-I{d}',f'-I{ROOT}',f'-I{ROOT/"src"}',f'-I{ROOT/"include"}',str(d/'check.cpp'),'-o',str(d/'check')],check=True)
        subprocess.run([str(d/'check'),str(wav)],check=True,timeout=5)
    print('PASS: audio progresses without main-loop pumps, real WAV parsing, exact sample count, stop/restart and allocation failures')
if __name__=='__main__':main()
