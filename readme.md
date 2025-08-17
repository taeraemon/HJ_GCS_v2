
``` bash
pip install PyQt5 pyqtgraph PyOpenGL PyOpenGL_accelerate
```



``` markdown
# How protocols works

- GCS -> NC  (Telecommand)
    - Design
        - :    -> Command Start
        - ID   -> Command ID (SV, MV)
        - ;    -> Separator
        - IDX  -> Index of target (0 ~ N-1)
        - ;    -> Separator
        - DATA -> Command Data (0: OFF, 1: ON)
        - #    -> Command End

    - Example
        - :SV;0;1#
        - :SV;0;0#
        - :MV;0;180#
        - :MV;0;0#


- NC -> GCS  (Telemetry)
    - Design
        - CSV style.
        - end with \n

    - Example
        - 1.23,2.34,3.45,...,13.37\n
```