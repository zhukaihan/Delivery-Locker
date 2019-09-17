# -*- coding: utf-8 -*-

import wifinetctl as wifi


def Search():
    wifilist = []

    cells = wifi.Cell.all('wlan0')

    for cell in cells:
        wifilist.append(cell)

    return wifilist


def FindFromSearchList(ssid):
    wifilist = Search()

    for cell in wifilist:
        if cell.ssid == ssid:
            return cell

    return False


def FindFromSavedList(ssid):
    cell = wifi.Scheme.find('wlan0', ssid)

    if cell:
        return cell

    return False


def Connect(ssid, password=None):
    cell = FindFromSearchList(ssid)

    if cell:
        savedcell = FindFromSavedList(cell.ssid)

        # Already Saved from Setting
        if savedcell:
            try:
                savedcell.activate()
                return cell

            # Wrong Password, treat as new connect
            except wifi.exceptions.ConnectionError:
                Delete(ssid)

        # First time to connect
        if cell.encrypted:
            if password:
                scheme = Add(cell, password)

                try:
                    scheme.activate()

                # Wrong Password
                except wifi.exceptions.ConnectionError:
                    Delete(ssid)
                    return False

                return cell
            else:
                return False
        else:
            scheme = Add(cell)

            try:
                scheme.activate()
            except wifi.exceptions.ConnectionError:
                Delete(ssid)
                return False

            return cell
    
    return False


def Add(cell, password=None):
    if not cell:
        return False

    scheme = wifi.Scheme.for_cell('wlan0', cell.ssid, cell, password)
    scheme.save()
    return scheme


def Delete(ssid):
    if not ssid:
        return False

    cell = FindFromSavedList(ssid)

    if cell:
        cell.delete()
        return True

    return False


# Return True is the wifi has connected to a know network successfully. 
# Otherwise, it returns an array of cells that are connectable. 
def SearchAndConnectKnown():
    # get all cells from the air
    # wifiCells = Search()
    # ssids = [cell.ssid for cell in wifiCells]

    # schemes = list(wifi.Scheme.all("wlan0"))

    # for scheme in schemes:
    #     ssid = scheme.options.get('wpa-ssid', scheme.options.get('wireless-essid'))
    #     if ssid in ssids:
    #         try:
    #             scheme.activate()
    #             return True
    #         except:
    #             pass
    # return wifiCells

    wifiCells = Search()
    for cell in wifiCells:
        try:
            if FindFromSavedList(cell.ssid):
                if Connect(cell.ssid):
                    return True
        except:
            pass
    return wifiCells


if __name__ == '__main__':
    Delete("MySpectrumWiFifb-2G")
    Delete("MySpectrumWiFifb-5G")
    # Search WiFi and return WiFi list
    # print(SearchAndConnectKnown())
    # print(Connect("MySpectrumWiFifb-5G", "hockeypraise107"))

    # Connect WiFi with password & without password
    # print Connect('OpenWiFi')
    # print Connect('ClosedWiFi', 'password')

    # # Delete WiFi from auto connect list
    # print Delete('DeleteWiFi')
