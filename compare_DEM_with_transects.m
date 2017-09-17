% compare_DEM_with_transects - Script to compare DEM
% location of input and output files
dv = 'd:'
dn = '\crs\proj\2017_Ontario\2017-07-13_Sodus_North'

% filenames for transect points and file exported from Global Mapper, and
% desired output filename
fn_trans = '2017-07-13-Sodus_North_trans.txt'
fn_dem = 'sodus_north_dem_values_at_transect_points.csv'
fn_out = 'transect_minus_dem.txt'
% text for graph title
ttext = 'Sodus North'

fp_trans = fullfile(dv,dn,fn_trans)
fp_dem = fullfile(dv,dn,fn_dem)
fp_out = fullfile(dv,dn,fn_out)

%% Read the transect file (measured values)
delimiter = ',';
% Read columns of data as text:
% For more information, see the TEXTSCAN documentation.
formatSpec = '%s%s%s%s%s%s%s%[^\n\r]';
% Open the text file.
fileID = fopen(fp_trans,'r');
% Read columns of data according to the format.
% This call is based on the structure of the file used to generate this
% code. If an error occurs for a different file, try regenerating the code
% from the Import Tool.
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);
% Close the text file.
fclose(fileID);
% Convert the contents of columns containing numeric text to numbers.
% Replace non-numeric text with NaN.
raw = repmat({''},length(dataArray{1}),length(dataArray)-1);
for col=1:length(dataArray)-1
   raw(1:length(dataArray{col}),col) = dataArray{col};
end
numericData = NaN(size(dataArray{1},1),size(dataArray,2));

for col=[1,2,3,4,5,6]
   % Converts text in the input cell array to numbers. Replaced non-numeric
   % text with NaN.
   rawData = dataArray{col};
   for row=1:size(rawData, 1);
      % Create a regular expression to detect and remove non-numeric prefixes and
      % suffixes.
      regexstr = '(?<prefix>.*?)(?<numbers>([-]*(\d+[\,]*)+[\.]{0,1}\d*[eEdD]{0,1}[-+]*\d*[i]{0,1})|([-]*(\d+[\,]*)*[\.]{1,1}\d+[eEdD]{0,1}[-+]*\d*[i]{0,1}))(?<suffix>.*)';
      try
         result = regexp(rawData{row}, regexstr, 'names');
         numbers = result.numbers;
         
         % Detected commas in non-thousand locations.
         invalidThousandsSeparator = false;
         if any(numbers==',');
            thousandsRegExp = '^\d+?(\,\d{3})*\.{0,1}\d*$';
            if isempty(regexp(numbers, thousandsRegExp, 'once'));
               numbers = NaN;
               invalidThousandsSeparator = true;
            end
         end
         % Convert numeric text to numbers.
         if ~invalidThousandsSeparator;
            numbers = textscan(strrep(numbers, ',', ''), '%f');
            numericData(row, col) = numbers{1};
            raw{row, col} = numbers{1};
         end
      catch me
      end
   end
end

% Split data into numeric and cell columns.
rawNumericColumns = raw(:, [1,2,3,4,5,6]);
rawCellColumns = raw(:, 7);

% Allocate imported array to column variable names
Id = cell2mat(rawNumericColumns(:, 1));
y = cell2mat(rawNumericColumns(:, 2));
x = cell2mat(rawNumericColumns(:, 3));
zm = cell2mat(rawNumericColumns(:, 4));
% Don't need the following data:
%Longitude = cell2mat(rawNumericColumns(:, 5));
%Latitude = cell2mat(rawNumericColumns(:, 6));
%Label = rawCellColumns(:, 1);

% Clear temporary variables
clearvars filename delimiter formatSpec fileID dataArray ans raw col numericData rawData row regexstr result numbers invalidThousandsSeparator thousandsRegExp me rawNumericColumns rawCellColumns;

%% Read the xyz file exported from Global Mapper (DEM values)
% (much easier because it is all numbers
D = load(fp_dem);

%% calculate the difference
% x and y should be the same in both files.
z = D(:,3); % DEM
dz = z-zm;

%% write the results out to a CSV file
fid = fopen(fp_out, 'w')
for i=1:length(D)
   fprintf(fid,'%f, %f, %f\n',y(i),x(i),dz(i))
end
fclose(fid)
%%
% some colors
gray = [.2 .2 .2]
green = [.2 .7 .2]
red = [.7 .2 .2]

% remove points with huge diff (usually missing from DEM)
dz(find(abs(dz)>5))=NaN;
set(0,'defaulttextfontsize',24)
set(0,'defaultaxesfontsize',18)

stats=nandist(dz);
figure(1);clf
h=histogram(dz,[-.51:.02:.51],'normalization','probability');
set(h,'facecolor',gray)
xlim([-.205 .205])
ylim([0 .4])
% ylabel('\itN')
ylabel('Fraction of Observations')
xlabel('DEM minus Survey Point (m)')
title(ttext)
stx = sprintf('N    =% 3d\nMean =%7.3f\nRMS  =%7.3f\nMAD  =%7.3f\nMin  =%7.3f\nMax  =%7.3f',...
   stats.n,stats.mean,stats.rms,stats.mad,stats.min,stats.max)
ht=text(.07,.25,stx)
set(ht,'fontsize',14)
if(0)
   % make a little scatter plot of diffs
   hold on
   xoff = min(x);
   yoff = min(y)+4;
   sf = (max(x)-min(x))/.3;
   xt = ((x-xoff)/sf)-0.4;
   yt = (y-yoff)/(sf/10)+10;
   scatter(xt,yt,24,dz,'filled')
   caxis([-.4 .4])
   colormap(ccmap)
end
