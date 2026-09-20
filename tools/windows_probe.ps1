$Targets = @(
    @{
        VID  = "2516"
        PID  = "0228"
        Role = "HAF 700 EVO 2025 LCD"
    },
    @{
        VID  = "2516"
        PID  = "01C9"
        Role = "ARGB GEN-2 Controller"
    }
)

foreach ($Target in $Targets) {

    $Pattern = "VID_$($Target.VID)&PID_$($Target.PID)"

    Write-Host ""
    Write-Host "=== $($Target.Role) ==="
    Write-Host "USB ID: $($Target.VID):$($Target.PID)"
    Write-Host ""

    $Devices = Get-PnpDevice -PresentOnly |
        Where-Object {
            $_.InstanceId -match $Pattern
        }

    if (-not $Devices) {
        Write-Host "Device not detected."
        continue
    }

    foreach ($Device in $Devices) {

        $BusDescription = (
            Get-PnpDeviceProperty `
                -InstanceId $Device.InstanceId `
                -KeyName "DEVPKEY_Device_BusReportedDeviceDesc" `
                -ErrorAction SilentlyContinue
        ).Data

        [PSCustomObject]@{
            Status         = $Device.Status
            Class          = $Device.Class
            FriendlyName   = $Device.FriendlyName
            BusDescription = $BusDescription
            InstanceId     = $Device.InstanceId
        }
    }
}
