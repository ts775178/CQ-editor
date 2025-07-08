import cadquery as cq
print(cq.__version__)
print(type(cq.Workplane("XY").box(1,1,1).val().wrapped))