
from   hashlib     import sha1
from   binascii    import b2a_base64
from   struct      import pack
from   _thread     import start_new_thread
import gc

class MicroWebSocket :

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    _handshakeSign = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    _opContFrame   = 0x0
    _opTextFrame   = 0x1
    _opBinFrame    = 0x2
    _opCloseFrame  = 0x8
    _opPingFrame   = 0x9
    _opPongFrame   = 0xA
    
    _msgTypeText   = 1
    _msgTypeBin    = 2

    # ============================================================================
    # ===( Utils  )===============================================================
    # ============================================================================

    def _tryAllocByteArray(size) :
        for x in range(10) :
            try :
                gc.collect()
                return bytearray(size)
            except :
                pass
        return None

    # ----------------------------------------------------------------------------

    def _tryStartThread(func, args=()) :
        for x in range(10) :
            try :
                gc.collect()
                start_new_thread(func, args)
                return True
            except :
                pass
        return False

    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__(self, socket, httpClient, httpResponse, maxRecvLen, threaded, acceptCallback) :
        self._socket            = socket
        self._httpCli           = httpClient
        self._closed            = True
        self.RecvTextCallback   = None
        self.RecvBinaryCallback = None
        self.ClosedCallback     = None
        if self._handshake(httpResponse) :
            self._ctrlBuf = MicroWebSocket._tryAllocByteArray(0x7D)
            self._msgBuf  = MicroWebSocket._tryAllocByteArray(maxRecvLen)
            if self._ctrlBuf and self._msgBuf :
                self._msgType = None
                self._msgLen  = 0
                if threaded :
                    if MicroWebSocket._tryStartThread(self._wsProcess, (acceptCallback, )) :
                        return
                else :
                    self._wsProcess(acceptCallback)
                    return
            print("MicroWebSocket : Out of memory on new WebSocket connection.")
        try :
            self._socket.close()
        except :
            pass

    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    def _handshake(self, httpResponse) :
        try :
            key = self._httpCli.GetRequestHeaders().get('Sec-WebSocket-Key', None)
            if key :
                r = sha1(key + self._handshakeSign).digest()
                r = b2a_base64(r).decode()
                httpResponse.WriteSwitchProto("websocket", { "Sec-WebSocket-Accept" : r })
                return True
        except :
            pass
        return False

    # ----------------------------------------------------------------------------

    def _wsProcess(self, acceptCallback) :
        self._socket.settimeout(3600)
        self._closed = False
        try :
            acceptCallback(self, self._httpCli)
        except Exception as ex :
            print("MicroWebSocket : Error on accept callback (%s)." % str(ex))
        while not self._closed :
            if not self._receiveFrame() :
                self.Close()
        if self.ClosedCallback :
            try :
                self.ClosedCallback(self)
            except Exception as ex :
                print("MicroWebSocket : Error on closed callback (%s)." % str(ex))

    # ----------------------------------------------------------------------------

    def _receiveFrame(self) :
        try :

            b = self._socket.read(2)
            if not b or len(b) != 2 :
                return False

            fin    = b[0] & 0x80 > 0
            opcode = b[0] & 0x0F
            masked = b[1] & 0x80 > 0
            length = b[1] & 0x7F

            if opcode == self._opContFrame and not self._msgType :
                return False
            elif opcode == self._opTextFrame :
                self._msgType = self._msgTypeText
            elif opcode == self._opBinFrame :
                self._msgType = self._msgTypeBin

            if length == 0x7E :
                b = self._socket.read(2)
                if not b or len(b) != 2 :
                    return False
                length = (b[0] << 8) + b[1]
            elif length == 0x7F :
                return False

            mask = self._socket.read(4) if masked else None
            if masked and (not mask or len(mask) != 4) :
                return False

            if opcode == self._opContFrame or \
               opcode == self._opTextFrame or \
               opcode == self._opBinFrame :

                if length > 0 :
                    buf = memoryview(self._msgBuf)[self._msgLen:]
                    if length > len(buf) :
                        return False
                    if self._socket.readinto(buf, length) != length :
                        return False
                    if masked :
                        for i in range(length) :
                            idx = self._msgLen + i
                            self._msgBuf[idx] ^= mask[i%4]
                    self._msgLen += length
                    if fin :
                        b = bytes(memoryview(self._msgBuf)[:self._msgLen])
                        if self._msgType == self._msgTypeText :
                            if self.RecvTextCallback :
                                try :
                                    self.RecvTextCallback(self, b.decode())
                                except Exception as ex :
                                    print("MicroWebSocket : Error on recv text callback (%s)." % str(ex))
                        else :
                            if self.RecvBinaryCallback :
                                try :
                                    self.RecvBinaryCallback(self, b)
                                except Exception as ex :
                                    print("MicroWebSocket : Error on recv binary callback (%s)." % str(ex))
                        self._msgType = None
                        self._msgLen  = 0
                else :
                    return False

            elif opcode == self._opPingFrame :

                if length > len(self._ctrlBuf) :
                    return False
                if length > 0 :
                    if self._socket.readinto(self._ctrlBuf, length) != length :
                        return False
                    pingData = memoryview(self._ctrlBuf)[:length]
                else :
                    pingData = None
                self._sendFrame(self._opPongFrame, pingData)

            elif opcode == self._opCloseFrame :
                self.Close()

        except :
            return False

        return True

    # ----------------------------------------------------------------------------

    def _sendFrame(self, opcode, data=None, fin=True) :
        if not self._closed and opcode >= 0x00 and opcode <= 0x0F :
            dataLen = 0 if not data else len(data)
            if dataLen <= 0xFFFF :
                b1 = (0x80 | opcode) if fin else opcode
                b2 = 0x7E if dataLen >= 0x7E else dataLen
                try :
                    if self._socket.write(pack('>BB', b1, b2)) == 2 :
                        if dataLen > 0 :
                            if dataLen >= 0x7E :
                                self._socket.write(pack('>H', dataLen))
                            return self._socket.write(data) == dataLen
                        else :
                            return True
                except :
                    pass
        return False

    # ----------------------------------------------------------------------------

    def SendText(self, msg) :
        return self._sendFrame(self._opTextFrame, msg.encode())

    # ----------------------------------------------------------------------------

    def SendBinary(self, data) :
        return self._sendFrame(self._opBinFrame, data)

    # ----------------------------------------------------------------------------

    def IsClosed(self) :
        return self._closed

    # ----------------------------------------------------------------------------

    def Close(self) :
        if not self._closed :
            try :
                self._sendFrame(self._opCloseFrame)
                self._socket.close()
                self._closed = True
            except :
                pass

    # ============================================================================
    # ============================================================================
    # ============================================================================

