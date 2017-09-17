% Script to summarize files with camera settings
% The camera settings were extracted from the EXIF info using EXIFTools:
% exiftool -csv -aperture -shutterspeed -iso *.JPG > ..\f44cam.csv

fnout = 'camsettings.csv'
fid = fopen(fnout,'w');
fprintf(fid,'Flight, NumImages, ISO, Aperture, ShutterSpeed_5pct, ShutterSpeed_50pct\n')

flist = dir('f*cam.csv');
for k = 1:length(flist)
   filename = flist(k).name
   disp(filename)
   % Read the .csv file
   delimiter = ',';
   startRow = 2;
   formatSpec = '%s%f%s%f%[^\n\r]';
   fileID = fopen(filename,'r');
   dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter, 'HeaderLines' ,startRow-1, 'ReturnOnError', false, 'EndOfLine', '\r\n');
   fclose(fileID);
   
   % Allocate imported array to column variable names
   SourceFile = dataArray{:, 1};
   Aperture = dataArray{:, 2};
   ShutterSpeed_text = dataArray{:, 3};
   ISO = dataArray{:, 4};
   
   % Clear temporary variables
   clearvars filename delimiter startRow formatSpec fileID dataArray ans;
   
   % Convert shutter speed to a number
   nimages = length(ISO)
   ShutterSpeed = zeros(nimages,1);
   for i=1:nimages
      ShutterSpeed(i)=1./eval(ShutterSpeed_text{i});
   end
   %
   ISO_d=dist(ISO);
   Ap_d =dist(Aperture);
   SP_d =dist(ShutterSpeed);
   
   fprintf(fid,'%s, %d, %d, %.1f, %6.1f, %6.1f\n',...
      flist(k).name,ISO_d.n,ISO_d.pct50,Ap_d.pct50,SP_d.pct5,SP_d.pct50) 
end
fclose(fid);